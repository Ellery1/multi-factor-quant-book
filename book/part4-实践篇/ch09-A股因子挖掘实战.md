# 第9章：A股因子挖掘实战——用真实数据构建因子库

> **前置知识**：第3-6章理论篇（因子定义、检验方法、合成理论）；第7-8章工具篇（数据获取、回测框架）
>
> **学习目标**：将理论篇的方法论应用于A股真实数据；完成从"计算因子值"到"判定因子有效性"的全流程；建立一个包含5-10个有效因子的因子库；理解筛选决策的逻辑

---

## 9.1 确定因子候选池：方法论

### 9.1.1 因子候选的来源

我们从三个来源构建候选因子池：

1. **经典学术因子**（第4章推导过的）：EP、BP、动量12-1、ROE、低波动
2. **变体因子**：SP（营收/市值）、CF/P（现金流/市值）、ROA、毛利率
3. **复合因子**：应计利润、盈利修正（分析师上调比例）、资产增长率

共计约15-20个候选因子。我们的目标是从中筛选出5-10个真正有效且互补的因子。

### 9.1.2 因子计算的标准化流程

对每个候选因子，执行统一的处理流程：

```python
def process_factor(raw_factor, industry):
    """因子值的标准化处理流程"""
    # Step 1: 去极值（Winsorize，缩尾处理）
    lower = raw_factor.quantile(0.01)
    upper = raw_factor.quantile(0.99)
    factor = raw_factor.clip(lower, upper)
    
    # Step 2: 行业中性化（可选——去掉行业影响）
    # 在每个行业内做标准化，消除"某个行业整体PE低"的干扰
    factor = factor.groupby(industry).transform(lambda x: (x - x.mean()) / x.std())
    
    # Step 3: 标准化（整体均值0、标准差1）
    factor = (factor - factor.mean()) / factor.std()
    
    return factor
```

**为什么要去极值？** 极端值（如亏损股的PE为负值或极大值）会扭曲排名和回归结果。缩尾处理将1%以下和99%以上的值限制在边界上。

**为什么要行业中性化？** 银行业的PE普遍在5-8倍，科技业在30-60倍。如果不做行业中性化，"低PE策略"会变成"全买银行股"——你以为在选便宜股，实际在做行业赌注。

---

## 9.2 因子计算流水线

### 9.2.1 价值因子计算

```python
def calc_value_factors(financial_data, market_data):
    """计算价值类因子"""
    factors = pd.DataFrame()
    
    # EP = 净利润TTM / 总市值
    factors['EP'] = financial_data['net_profit_ttm'] / market_data['total_mv']
    
    # BP = 净资产 / 总市值
    factors['BP'] = financial_data['total_equity'] / market_data['total_mv']
    
    # SP = 营业收入TTM / 总市值
    factors['SP'] = financial_data['revenue_ttm'] / market_data['total_mv']
    
    # CF/P = 经营现金流TTM / 总市值
    factors['CFP'] = financial_data['ocf_ttm'] / market_data['total_mv']
    
    return factors
```

### 9.2.2 动量因子计算

```python
def calc_momentum_factor(price_data):
    """计算动量因子：过去12个月收益率（跳过最近1个月）"""
    # 12个月前的价格 / 1个月前的价格 - 1
    ret_12m = price_data.shift(21) / price_data.shift(252) - 1  # 约21交易日/月
    return ret_12m
```

### 9.2.3 质量因子计算

```python
def calc_quality_factors(financial_data):
    """计算质量类因子"""
    factors = pd.DataFrame()
    
    # ROE = 净利润TTM / 平均净资产
    factors['ROE'] = financial_data['net_profit_ttm'] / financial_data['avg_equity']
    
    # 毛利/总资产 (Gross Profitability, GP/A, Novy-Marx 2013)
    # 注意：这不是传统的"毛利率"(毛利/营收)，而是毛利润除以总资产
    factors['GP_A'] = (financial_data['revenue_ttm'] - financial_data['cogs_ttm']) / financial_data['total_assets']
    
    # 应计利润率 = (净利润 - 经营现金流) / 总资产
    factors['ACCRUALS'] = -(financial_data['net_profit_ttm'] - financial_data['ocf_ttm']) / financial_data['total_assets']
    # 注意取负号：低应计(高现金流质量)方向为正
    
    return factors
```

---

## 9.3 单因子IC检验

### 9.3.1 逐月计算IC

```python
from scipy import stats

def calc_monthly_ic(factor_df, return_df):
    """
    计算每月的IC（Spearman秩相关）
    factor_df: 月末因子值, index=日期, columns=股票
    return_df: 下月收益率, index=日期, columns=股票
    """
    ic_series = {}
    for date in factor_df.index:
        if date not in return_df.index:
            continue
        f = factor_df.loc[date].dropna()
        r = return_df.loc[date].reindex(f.index).dropna()
        common = f.index.intersection(r.index)
        if len(common) < 30:  # 最少30只股票
            continue
        ic, _ = stats.spearmanr(f[common], r[common])
        ic_series[date] = ic
    return pd.Series(ic_series)
```

### 9.3.2 IC检验结果汇总

对所有候选因子运行IC检验后，汇总结果：

| 因子 | IC均值 | IC标准差 | IR | t值 | 胜率 |
|------|--------|---------|-----|-----|------|
| EP | 0.048 | 0.072 | 0.67 | 7.3 | 62% |
| BP | 0.035 | 0.080 | 0.44 | 4.8 | 58% |
| SP | 0.032 | 0.075 | 0.43 | 4.7 | 56% |
| CF/P | 0.041 | 0.068 | 0.60 | 6.6 | 60% |
| 动量12-1 | 0.028 | 0.095 | 0.29 | 3.2 | 54% |
| ROE | 0.038 | 0.065 | 0.58 | 6.4 | 61% |
| GP/A(毛利/总资产) | 0.035 | 0.060 | 0.58 | 6.4 | 60% |
| 应计(负) | 0.025 | 0.070 | 0.36 | 3.9 | 55% |
| 低波动 | 0.030 | 0.082 | 0.37 | 4.0 | 55% |

*注：以上为示意数据，基于A股2014-2023年沪深300成分股估计。*

**筛选标准**（参照第5章的方法论）：
- $|t| > 3.0$（通过HLZ多重检验调整）：✓ 全部通过
- $IR > 0.4$：EP、CF/P、ROE、毛利/资产通过
- 胜率 > 55%：大部分通过

---

## 9.4 分层回测验证

对通过IC检验的因子，进一步做分5层回测验证单调性：

```python
def layered_backtest(factor_df, return_df, n_groups=5):
    """分层回测：按因子值分n组，计算每组的平均月收益"""
    group_returns = {f'G{i+1}': [] for i in range(n_groups)}
    
    for date in factor_df.index:
        f = factor_df.loc[date].dropna()
        r = return_df.loc[date].reindex(f.index).dropna()
        common = f.index.intersection(r.index)
        
        if len(common) < n_groups * 10:
            continue
        
        # 按因子值分组
        groups = pd.qcut(f[common], n_groups, labels=False)
        
        for g in range(n_groups):
            stocks_in_group = groups[groups == g].index
            group_returns[f'G{g+1}'].append(r[stocks_in_group].mean())
    
    return pd.DataFrame({k: pd.Series(v) for k, v in group_returns.items()})
```

**EP因子的分层结果**（示意）：

| G1(低EP/贵) | G2 | G3 | G4 | G5(高EP/便宜) | G5-G1 |
|-------------|-----|-----|-----|--------------|-------|
| 0.5%/月 | 0.8% | 1.0% | 1.3% | 1.8% | 1.3% |

从G1到G5严格单调递增 → EP因子通过分层回测检验。

---

## 9.5 因子筛选：从候选到入选

### 9.5.1 筛选决策逻辑

通过以下漏斗进行筛选：

```
15-20个候选因子
    ↓ IC显著性（t > 3）
12-15个通过
    ↓ IR > 0.4
8-10个通过
    ↓ 分层单调性检验
7-9个通过
    ↓ 去冗余（相关性 > 0.7的只保留IC更高的）
5-7个最终入选
```

### 9.5.2 去冗余：选择互补因子

EP和BP相关性0.7——它们大部分信息重叠。两者中选IC更高的（EP），剔除BP。

最终入选因子库（示例）：

| 因子 | 类别 | IC | IR | 保留理由 |
|------|------|-----|-----|---------|
| EP | 价值 | 0.048 | 0.67 | IC最高的价值因子 |
| CF/P | 价值(现金流) | 0.041 | 0.60 | 与EP相关性仅0.45，有增量 |
| 动量12-1 | 动量 | 0.028 | 0.29 | 与价值因子负相关，提供互补 |
| ROE | 质量 | 0.038 | 0.58 | 质量维度的代表 |
| GP/A(毛利/总资产) | 质量(另一维度) | 0.035 | 0.58 | 与ROE相关性仅0.4 |
| 低波动 | 波动率 | 0.030 | 0.37 | 独立维度 |

---

## 9.6 本章小结

### 9.6.1 内容回顾

1. 从15-20个候选因子中，通过IC检验→分层验证→去冗余，筛选出5-7个互补有效因子
2. 因子处理三步骤：去极值→行业中性化→标准化
3. 筛选核心标准：t > 3（统计显著）、IR > 0.4（足够稳定）、相关性 < 0.7（非冗余）
4. 最终因子库覆盖价值、动量、质量、波动率多个维度——确保互补性

---

### 9.6.2 常见陷阱

1. **不做行业中性化**：结果是"价值因子"变成了"买银行卖科技"——你在做行业轮动而非真正的因子选股。

2. **筛选后不做样本外验证**：用2014-2020年数据筛选因子，必须保留2021-2023年做独立验证——否则筛选过程本身就是"数据挖掘"。

3. **只看IC不看IR**：IC=0.06但标准差0.15的因子（IR=0.4）不如IC=0.04但标准差0.03的因子（IR=1.3）。

4. **保留高相关因子**：EP和BP都入选（相关性0.7）= 给同一个信号双倍权重。用了等于没用多因子——变成了"价值因子×2"。


---

## 补充：A股特殊数据处理

### ST股与退市风险股的处理

ST股票（因财务异常被特别处理的股票）通常具有极端的因子值——极低的PE/PB、极高的波动率。如果不做特殊处理，你的"价值因子"可能会选中大量濒临退市的垃圾股。

**处理规则**：在因子计算和选股之前，剔除以下股票：
- 当前被标记为ST或*ST的
- 上市不满6个月的（次新股效应污染）
- 当月停牌超过5个交易日的

```python
def filter_tradeable(stock_pool, date):
    """剔除不可交易或有特殊状态的股票"""
    pool = stock_pool.copy()
    pool = pool[~pool['is_st']]            # 剔除ST
    pool = pool[pool['list_days'] > 120]    # 剔除上市不满6个月
    pool = pool[pool['suspend_days'] < 5]   # 剔除长期停牌
    return pool
```

### 次新股效应

A股新股上市后通常经历一段"炒新"行情（连续涨停→高位回落）。这段时间的价格行为与基本面无关，因子信号完全失效。

**推荐**：上市满6个月后才纳入因子计算池。

### 市值中性化

A股规模效应极强。如果不做市值中性化，很多因子的IC只是"规模的代理"——低PE的股票往往也是小市值的，你以为在做因子选股，实际只是在买小票。

**处理方法**：在行业中性化之后，再对市值做正交化：

```python
def market_cap_neutralize(factor, log_market_cap):
    """对因子值做市值中性化（正交化）"""
    import statsmodels.api as sm
    X = sm.add_constant(log_market_cap)
    model = sm.OLS(factor, X, missing='drop').fit()
    return model.resid  # 残差 = 去掉市值影响后的"纯因子"
```

中性化后的因子 = 原始因子中**不能被市值解释**的部分。如果残差IC仍然显著→因子有独立于规模的增量预测力；如果残差IC接近零→因子只是规模的化身，可以剔除。