# 附录A：量化系统设计蓝图

> 本附录为有一定 Python 开发经验的读者提供一个可直接参考的系统设计方案。它不涉及任何数学推导，仅描述"你的代码应该怎么组织"。如果你想跳过数学模型直接搭系统，从这里开始。

---

## A.1 系统总体架构

系统采用分层架构，数据自顶向下流动，核心决策自底向上输出。左侧为实盘/定时任务的数据链路，中间为主数据流，右侧为回测的独立数据链路。风险监控和工具模块贯穿全局。

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                         ⏰ 定时任务 (Scheduler)                          │
 │         数据更新 · 因子重算 · 调仓执行 · 邮件通知 · 异常报警              │
 └──────┬──────────────────────────────────────────────────────────────────┘
        │                                    ┌──────────────────────────┐
        ▼                                    │     📊 回测 (Backtest)   │
 ┌──────────────────┐                        │  事件驱动引擎 · 历史数据  │
 │  📡 数据获取       │                        │  回放 · 模拟券商扣费     │
 │  tushare/akshare  │◄─ 拉取实时数据          │  绩效报告生成            │
 │  本地缓存          │                        │                          │
 └────────┬─────────┘                        │  回测数据从本地DB读取，   │
          │                                   │  不经API，但复用同一套    │
          ▼                                   │  清洗和因子计算流程       │
 ┌──────────────────────────────────────────────────────────────────────┐
 │                      🧹 数据处理 (Data Pipeline)                      │
 │  格式标准化 · 复权对齐 · 停牌/ST/次新股过滤 · 财报时间对齐 · 完整性检查  │
 └────────────────────────────────┬─────────────────────────────────────┘
                                  │  标准化行情 + 财务数据
                                  ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                      📐 因子计算 (Factors)                             │
 │                                                                       │
 │  ┌─ 因子值计算 ──────────────────────────────────────────────┐        │
 │  │  EP · BP · SP · CF/P   价值因子                           │        │
 │  │  12M动量 · 1M反转       动量因子                           │        │
 │  │  ROE · 毛利率 · 应计    质量因子                           │        │
 │  │  60日波动率 · 换手率    低波动因子                          │        │
 │  │  log(total_mv)         规模因子                            │        │
 │  └───────────────────────────────────────────────────────────┘        │
 │                                                                       │
 │  ┌─ 因子预处理 ──────────────────────────────────────────────┐        │
 │  │  去极值 (winsorize) → 行业中性化 → 市值正交化 → 标准化 (z-score)  │
 │  └───────────────────────────────────────────────────────────┘        │
 │                                                                       │
 │  ┌─ 因子检验 ────────────────────────────────────────────────┐        │
 │  │  IC均值/t值/IR · 分层回测 · 单调性 ·                         │        │
 │  │  多重检验校正(Bonferroni/FDR) · 因子相关性矩阵 · 去冗余筛选      │        │
 │  └───────────────────────────────────────────────────────────┘        │
 │                                                                       │
 │  ┌─ 因子处理 ────────────────────────────────────────────────┐        │
 │  │  对称正交化(§6.4) · IC半衰期监测(§5.6) · 因子拥挤度追踪        │        │
 │  └───────────────────────────────────────────────────────────┘        │
 └────────────────────────────────┬─────────────────────────────────────┘
                                  │  正交化后的标准化因子值
                                  ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │                      🎯 策略引擎 (Strategy)                            │
 │                                                                       │
 │  ┌─ 因子合成 (§6.2-§6.6) ────────────────────────────────────┐        │
 │  │  等权(基准) → 收缩IC加权(Ledoit-Wolf) → 贝叶斯动态加权        │        │
 │  └───────────────────────────────────────────────────────────┘        │
 │                                                                       │
 │  ┌─ 组合构建 (§8.3) ────────────────────────────────────────┐        │
 │  │  综合得分排名 · Top N 选股 · 等权/得分加权 ·                    │        │
 │  │  行业约束(±5%) · 个股权重上限 · 最小持仓检查                    │        │
 │  └───────────────────────────────────────────────────────────┘        │
 │                                                                       │
 │  ┌─ 调仓决策 (§8.4) ────────────────────────────────────────┐        │
 │  │  缓冲区规则(进入/退出双阈值) · 换手率平滑(α=0.1~0.3)           │        │
 │  └───────────────────────────────────────────────────────────┘        │
 │                                                                       │
 │  ┌─ 执行 (§7.3) ────────────────────────────────────────────┐        │
 │  │  可交易性检查(停牌/涨停) · 订单生成 · 交易日志记录                │        │
 │  └───────────────────────────────────────────────────────────┘        │
 └────────────────────────────────┬─────────────────────────────────────┘
                                  │  持仓指令 + 交易日志
                                  ▼
                      ┌───────────────────────┐
                      │   📬 邮件通知 / 报告    │
                      └───────────────────────┘
```

```
 ╔═══════════════════════╗    ╔═══════════════════════╗
 ║  🛡 风险监控 (Risk)    ║    ║  🔧 工具模块 (Utils)   ║
 ║                       ║    ║                       ║
 ║  过拟合检测(DSR/清单)  ║    ║  交易日历              ║
 ║  Walk-Forward 验证结果 ║    ║  日志系统              ║
 ║  最大回撤实时追踪       ║    ║  配置管理(yaml/.env)   ║
 ║  年化换手率监控         ║    ║  可视化(matplotlib)    ║
 ║  因子拥挤度预警         ║    ║  数据库DAO             ║
 ║                       ║    ║                       ║
 ║  (旁路模式，读取各层    ║    ║  (被所有层调用)        ║
 ║   输出但不阻塞主流程)   ║    ║                       ║
 ╚═══════════════════════╝    ╚═══════════════════════╝
```

各层的职责边界：
- **定时任务**：驱动整个系统的时钟。控制数据更新频率（日频/月频）、因子重算周期、调仓执行时间点。支持邮件通知和异常报警。
- **数据获取层**：只负责拉数据，不做任何计算或清洗。实盘通过 API 拉取，回测从本地 DB 读取。两个数据路径在此层分叉，但从数据处理层开始共享同一套代码。
- **数据处理层**：把不同来源的原始格式统一为系统内部标准格式。实盘处理增量数据（今天新增的行情），回测处理历史全量数据（但逐期切片的逻辑相同）。
- **因子计算层**：输入是标准化后的行情和财务数据，输出是每只股票在每个因子上的 z-score。包含四个子模块：因子值计算、预处理、检验、处理。回测和实盘共享完全相同的因子计算逻辑，确保一致性。
- **策略引擎层**：输入是正交化后的因子值，输出是"明天买什么、各买多少"。包含因子合成、组合构建、调仓决策、执行四个子模块。
- **风险监控层**：旁路模式运行，持续读取各层中间输出但不阻塞主流程。覆盖过拟合检测、回撤追踪、换手率监控、因子拥挤预警。
- **工具模块**：被所有层调用的通用基础设施。

---

## A.2 技术架构

推荐的技术栈（以 Python 生态为主）：

| 层级 | 推荐技术 | 备选 |
|------|---------|------|
| 数据获取 | `tushare` | `akshare` |
| 本地存储 | SQLite（`sqlite3` 标准库） | PostgreSQL（数据量>10GB 时） |
| 数据处理 | `pandas` | `polars`（高性能场景） |
| 数值计算 | `numpy` + `scipy` | — |
| 回测引擎 | 自研事件驱动框架 | `backtrader`、`zipline` |
| 可视化 | `matplotlib` + `seaborn` | `plotly`（交互式） |
| 任务调度 | `schedule` / cron | Airflow（规模化后） |
| 邮件通知 | `smtplib` + `email`（标准库） | — |
| 配置管理 | `PyYAML` + `.env` | — |
| 日志 | `logging` 标准库 | — |

### 项目目录结构

```
quant_system/
├── config/
│   ├── settings.yaml          # 策略参数、数据源配置
│   └── factor_registry.yaml   # 因子定义（名称、公式、数据依赖）
├── scheduler/
│   ├── __init__.py
│   ├── jobs.py                # 定时任务定义（数据更新/因子重算/调仓）
│   └── mailer.py              # 邮件通知（调仓报告/异常报警）
├── data_fetcher/
│   ├── __init__.py
│   ├── base.py                # 抽象基类：定义统一接口
│   ├── tushare_client.py      # Tushare 实现（实盘）
│   └── akshare_client.py      # AKShare 实现（备用）
├── data_pipeline/
│   ├── __init__.py
│   ├── cleaner.py             # 缺失值、异常值处理
│   ├── normalizer.py          # 格式标准化（日期、代码后缀）
│   ├── adjuster.py            # 复权处理
│   └── aligner.py             # 财报时间对齐
├── factors/
│   ├── __init__.py
│   ├── base.py                # 因子基类
│   ├── value.py               # 估值因子（EP、BP、SP、CF/P）
│   ├── momentum.py            # 动量因子（12M动量、1M反转）
│   ├── quality.py             # 质量因子（ROE、毛利率、应计）
│   ├── volatility.py          # 低波动因子
│   ├── size.py                # 规模因子
│   ├── testing.py             # IC/IR/t值/分层回测/单调性检验
│   ├── preprocessing.py       # 去极值、行业中性化、市值正交化、标准化
│   └── orthogonalization.py   # 正交化（Gram-Schmidt + 对称）
├── strategy/
│   ├── __init__.py
│   ├── synthesis.py           # 因子合成（等权/收缩IC加权/贝叶斯动态）
│   ├── portfolio.py           # 组合构建（Top N选股、权重分配、约束检查）
│   ├── rebalance.py           # 调仓决策（缓冲区、换手率平滑）
│   └── executor.py            # 可交易性检查、订单生成、交易日志
├── risk/
│   ├── __init__.py
│   ├── overfit_detector.py    # 过拟合检测（DSR、参数敏感性、检测清单）
│   ├── walk_forward.py        # Walk-Forward 样本外验证
│   ├── crowding.py            # 因子拥挤度监测
│   ├── drawdown_monitor.py    # 回撤实时监控
│   └── turnover_tracker.py    # 年化换手率追踪
├── backtest/
│   ├── __init__.py
│   ├── engine.py              # 事件驱动回测引擎（主循环）
│   ├── broker.py              # 模拟券商（撮合、扣费、涨跌停约束）
│   ├── data_feeder.py         # 历史数据切片回放（逐期推送给因子层）
│   └── reporter.py            # 绩效报告（年化收益/夏普/最大回撤/换手率）
├── storage/
│   ├── __init__.py
│   ├── models.py              # 数据库表定义（SQLAlchemy 或原生 SQL）
│   └── dao.py                 # 数据访问对象
├── utils/
│   ├── __init__.py
│   ├── calendar.py            # 交易日历（含调仓日计算）
│   ├── logger.py              # 日志配置
│   ├── config_loader.py       # 配置加载（yaml + .env）
│   └── visualizer.py          # 图表生成（IC序列/分层收益/回撤曲线）
├── tests/                     # 单元测试（pytest）
│   ├── test_factors.py
│   ├── test_strategy.py
│   └── test_backtest.py
├── notebooks/                 # Jupyter 探索性分析
├── .env                       # API token（不提交 git）
├── run_live.py                # 实盘入口：定时任务启动
├── run_backtest.py            # 回测入口：指定日期区间运行
└── requirements.txt
```

---

## A.3 核心业务流程

### 月度调仓完整流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 月末收盘  │───→│ 数据更新  │───→│ 因子计算  │───→│ 因子预处理 │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                     │
                     ┌───────────────────────────────┘
                     ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐
              │ 正交化    │───→│ 因子合成  │───→│ 综合得分  │
              └──────────┘    └──────────┘    └──────────┘
                                                     │
                     ┌───────────────────────────────┘
                     ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐
              │ 选股排名  │───→│ 权重分配  │───→│ 约束检查  │
              └──────────┘    └──────────┘    └──────────┘
                                                     │
                     ┌───────────────────────────────┘
                     ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐
              │ 可交易性  │───→│ 生成指令  │───→│ 记录日志  │
              │ 检查      │    │          │    │          │
              └──────────┘    └──────────┘    └──────────┘
```

### 回测验证流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ 样本内    │───→│ 参数优化  │───→│ Walk-     │
│ (前70%)   │    │          │    │ Forward   │
└──────────┘    └──────────┘    └──────────┘
                                      │
              ┌───────────────────────┘
              ▼
       ┌──────────┐    ┌──────────┐    ┌──────────┐
       │ 过拟合    │───→│ 样本外   │───→│ 实盘模拟  │
       │ 检测      │    │ 验证     │    │ 预估     │
       └──────────┘    └──────────┘    └──────────┘
```

---

## A.4 数据库表设计

所有数据存储在单个 SQLite 文件 `quant_data.db` 中。

### A.4.1 股票基础信息表 `stock_basic`

| 字段 | 类型 | 说明 |
|------|------|------|
| `ts_code` | TEXT PRIMARY KEY | 股票代码，如 `000001.SZ` |
| `name` | TEXT | 股票名称 |
| `industry` | TEXT | 申万一级行业 |
| `list_date` | TEXT | 上市日期 `YYYYMMDD` |
| `delist_date` | TEXT | 退市日期（NULL 表示仍上市） |

```sql
CREATE TABLE stock_basic (
    ts_code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    industry TEXT,
    list_date TEXT NOT NULL,
    delist_date TEXT
);
```

### A.4.2 日频行情表 `daily_price`

| 字段 | 类型 | 说明 |
|------|------|------|
| `ts_code` | TEXT | 股票代码 |
| `trade_date` | TEXT | 交易日 `YYYYMMDD` |
| `open` | REAL | 开盘价 |
| `high` | REAL | 最高价 |
| `low` | REAL | 最低价 |
| `close` | REAL | 收盘价 |
| `volume` | REAL | 成交量（手） |
| `amount` | REAL | 成交额（千元） |
| `adj_factor` | REAL | 复权因子 |

```sql
CREATE TABLE daily_price (
    ts_code TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    amount REAL,
    adj_factor REAL,
    PRIMARY KEY (ts_code, trade_date)
);
```

### A.4.3 财务数据表 `financials`

| 字段 | 类型 | 说明 |
|------|------|------|
| `ts_code` | TEXT | 股票代码 |
| `report_period` | TEXT | 报告期 `YYYYMMDD`（如 `20231231`） |
| `ann_date` | TEXT | 实际公告日期 |
| `revenue` | REAL | 营业收入（元） |
| `net_profit` | REAL | 归母净利润（元） |
| `total_assets` | REAL | 总资产（元） |
| `net_equity` | REAL | 归母净资产（元） |
| `operating_cf` | REAL | 经营活动现金流净额（元） |

```sql
CREATE TABLE financials (
    ts_code TEXT NOT NULL,
    report_period TEXT NOT NULL,
    ann_date TEXT,
    revenue REAL,
    net_profit REAL,
    total_assets REAL,
    net_equity REAL,
    operating_cf REAL,
    PRIMARY KEY (ts_code, report_period)
);
```

### A.4.4 日频估值表 `daily_basic`

| 字段 | 类型 | 说明 |
|------|------|------|
| `ts_code` | TEXT | 股票代码 |
| `trade_date` | TEXT | 交易日 |
| `pe_ttm` | REAL | 市盈率（TTM） |
| `pb` | REAL | 市净率 |
| `total_mv` | REAL | 总市值（万元） |
| `circ_mv` | REAL | 流通市值（万元） |
| `turnover_rate` | REAL | 换手率（%） |

```sql
CREATE TABLE daily_basic (
    ts_code TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    pe_ttm REAL,
    pb REAL,
    total_mv REAL,
    circ_mv REAL,
    turnover_rate REAL,
    PRIMARY KEY (ts_code, trade_date)
);
```

### A.4.5 因子值表 `factor_values`

| 字段 | 类型 | 说明 |
|------|------|------|
| `ts_code` | TEXT | 股票代码 |
| `calc_date` | TEXT | 计算日期 |
| `factor_name` | TEXT | 因子名称（如 `EP`、`MOM_12M`） |
| `raw_value` | REAL | 原始因子值（去极值前） |
| `winsorized_value` | REAL | 去极值后 |
| `neutralized_value` | REAL | 行业/市值中性化后 |
| `normalized_value` | REAL | 标准化后（z-score） |

```sql
CREATE TABLE factor_values (
    ts_code TEXT NOT NULL,
    calc_date TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    raw_value REAL,
    winsorized_value REAL,
    neutralized_value REAL,
    normalized_value REAL,
    PRIMARY KEY (ts_code, calc_date, factor_name)
);
```

### A.4.6 持仓记录表 `portfolio_holdings`

| 字段 | 类型 | 说明 |
|------|------|------|
| `trade_date` | TEXT | 调仓生效日 |
| `ts_code` | TEXT | 股票代码 |
| `target_weight` | REAL | 目标权重（0~1） |
| `actual_weight` | REAL | 实际权重（考虑可交易性后） |
| `shares` | INTEGER | 持有股数 |

```sql
CREATE TABLE portfolio_holdings (
    trade_date TEXT NOT NULL,
    ts_code TEXT NOT NULL,
    target_weight REAL,
    actual_weight REAL,
    shares INTEGER,
    PRIMARY KEY (trade_date, ts_code)
);
```

### A.4.7 交易日志表 `trade_log`

| 字段 | 类型 | 说明 |
|------|------|------|
| `trade_date` | TEXT | 交易执行日期 |
| `ts_code` | TEXT | 股票代码 |
| `action` | TEXT | `BUY` / `SELL` |
| `price` | REAL | 成交价 |
| `shares` | INTEGER | 成交数量 |
| `reason` | TEXT | 调仓原因（`REBALANCE` / `STOP_LOSS` 等） |
| `status` | TEXT | 执行状态（`FILLED` / `LIMIT_UP_BLOCKED` / `SUSPENDED`） |

```sql
CREATE TABLE trade_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date TEXT NOT NULL,
    ts_code TEXT NOT NULL,
    action TEXT NOT NULL,
    price REAL,
    shares INTEGER,
    reason TEXT,
    status TEXT
);
```

---

## A.5 数据获取与更新策略

### 接口约定

所有数据获取模块必须实现以下统一接口：

```python
class BaseDataFetcher:
    def get_daily_price(self, ts_code: str, start: str, end: str) -> pd.DataFrame:
        """获取日频行情，字段名统一为 trade_date/open/high/low/close/volume/adj_factor"""
        raise NotImplementedError

    def get_financials(self, ts_code: str, report_period: str) -> pd.DataFrame:
        """获取财务数据"""
        raise NotImplementedError

    def get_stock_basic(self) -> pd.DataFrame:
        """获取全市场股票基础信息"""
        raise NotImplementedError

    def get_daily_basic(self, trade_date: str) -> pd.DataFrame:
        """获取某交易日的估值和市值数据"""
        raise NotImplementedError

    def get_trade_cal(self, start: str, end: str) -> pd.DataFrame:
        """获取交易日历"""
        raise NotImplementedError
```

Tushare 和 AKShare 的实现各自继承此基类，数据处理层只依赖接口而非具体实现。

### 增量更新逻辑

```
1. 查询本地数据库中已存储的最新交易日 latest_date
2. 调用 API 获取 latest_date 到今天的全部新增数据
3. 对新增数据做清洗和标准化
4. INSERT 或 REPLACE 到对应表中
5. 更新 stock_basic 中可能新增或退市的股票
```

---

## A.6 关键算法的实现指引

以下算法在正文中有详细推导，此处给出实现入口和对应的章节引用：

| 步骤 | 核心算法 | 章节参考 | 实现要点 |
|------|---------|---------|---------|
| 去极值 | Winsorize（1%/99% 分位数截断） | ch05 §5.1 | `scipy.stats.mstats.winsorize` |
| 行业中性化 | 行业内 z-score 标准化 | ch08 §8.1.2 | 按申万行业分组后 groupby.transform |
| 市值中性化 | 因子值对对数市值做 OLS 回归取残差 | ch08 §8.1.3 | `statsmodels.api.OLS`，注意加入截距项 |
| IC 检验 | Spearman 秩相关 | ch05 §5.2 | `scipy.stats.spearmanr`，注意排缺失值 |
| 多重检验校正 | Bonferroni / BH-FDR | ch05 §5.5.2 | `statsmodels.stats.multitest.multipletests` |
| 正交化 | Gram-Schmidt / 对称正交化 | ch06 §6.4 | GS 可用循环实现；对称需 `scipy.linalg.sqrtm` |
| 因子合成 | 等权 / IC 加权 / 收缩 IC 加权 | ch06 §6.2-§6.6 | 收缩用 Ledoit-Wolf: `sklearn.covariance.LedoitWolf` |
| 组合优化 | 约束条件下最大化因子暴露 | ch08 §8.3 | 等权最简单；如需优化用 `scipy.optimize.minimize` |
| 换手率控制 | 缓冲区 + 指数平滑 | ch06 §6.5.1 / ch08 §8.4 | 缓冲区用进入/退出双阈值 |
| Walk-Forward 验证 | 滚动窗口训练/预测 | ch05 §5.5.5 | 固定窗口长度，每步向前滚动 1 期 |
| 过拟合检测 | 参数敏感性 + Deflated Sharpe Ratio | ch10 §10.2-§10.4 | DSR 需自己实现，公式见 §10.2.2 |

---

## A.7 配置文件示例

### factor_registry.yaml

```yaml
factors:
  - name: EP
    category: value
    formula: 1 / pe_ttm
    data_deps: [daily_basic.pe_ttm]
    preprocessing: [winsorize, industry_neutralize, standardize]

  - name: BP
    category: value
    formula: 1 / pb
    data_deps: [daily_basic.pb]
    preprocessing: [winsorize, industry_neutralize, standardize]

  - name: MOM_12M
    category: momentum
    formula: close_t / close_{t-12} - 1
    data_deps: [daily_price.close]
    preprocessing: [winsorize, standardize]
    params:
      window: 12

  - name: ROE
    category: quality
    formula: net_profit_ttm / net_equity_latest
    data_deps: [financials.net_profit, financials.net_equity]
    preprocessing: [winsorize, industry_neutralize, standardize]

  - name: LOW_VOL
    category: volatility
    formula: -std(log_return, 60)
    data_deps: [daily_price.close]
    preprocessing: [winsorize, standardize]
    params:
      window: 60
```

### settings.yaml

```yaml
strategy:
  stock_pool: "000300.SH"        # 股票池：沪深300
  rebalance_freq: "monthly"      # 调仓频率
  top_n: 30                      # 持仓数量
  weight_scheme: "equal"         # 等权 / ic_weighted / shrinkage_ic
  buffer:
    entry_threshold: 25          # 进入门槛（排名前25才买入）
    exit_threshold: 35           # 退出门槛（排名跌出前35才卖出）

cost:
  commission: 0.00015            # 佣金万1.5
  stamp_duty: 0.0005             # 印花税（仅卖出）
  slippage: 0.001                # 滑点估算

backtest:
  start_date: "2019-01-01"
  end_date: "2024-12-31"
  initial_capital: 100000        # 初始资金（元）
  benchmark: "000300.SH"

data:
  primary_source: "tushare"
  cache_dir: "./data_cache/"
  update_on_start: true

risk:
  max_drawdown_warning: -0.15    # 回撤超15%报警
  turnover_limit: 2.0            # 年化换手率上限（警告阈值）
  crowding_threshold: 0.5        # 因子拥挤度阈值
```

---

## A.8 主程序入口示例

```python
# main.py
import yaml
from data_pipeline.cleaner import clean_and_store
from factors.preprocessing import preprocess_all
from factors.orthogonalization import symmetric_orthogonalize
from strategy.synthesis import synthesize
from strategy.rebalance import generate_target_portfolio
from strategy.executor import execute_rebalance
from risk.overfit_detector import check_parameter_sensitivity

def monthly_rebalance(date: str):
    """每月调仓的完整入口"""
    # 1. 数据更新（增量拉取）
    clean_and_store(date)

    # 2. 因子计算与预处理
    factors = preprocess_all(date)  # 去极值 → 行业中性化 → 标准化

    # 3. 正交化（去冗余）
    factors_orth = symmetric_orthogonalize(factors)

    # 4. 因子合成
    scores = synthesize(factors_orth, method="shrinkage_ic")

    # 5. 生成目标持仓
    target = generate_target_portfolio(scores, top_n=30, buffer=(25, 35))

    # 6. 执行调仓
    orders = execute_rebalance(target, date)

    # 7. 记录日志
    for order in orders:
        log_trade(order)

    # 8. 过拟合监控
    check_parameter_sensitivity()

if __name__ == "__main__":
    # 加载配置
    with open("config/settings.yaml") as f:
        config = yaml.safe_load(f)

    # 遍历回测区间内每个调仓日
    for date in rebalance_dates(config["backtest"]):
        monthly_rebalance(date)
```
