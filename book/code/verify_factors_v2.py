# -*- coding: utf-8 -*-
"""
核实5+6：五大因子相关性和溢价/夏普/回撤
策略：用沪深300成分股（数据量可控），逐股获取财务数据
"""
import os, time, json
import numpy as np
import pandas as pd
from pathlib import Path

env_path = Path(__file__).parent / '.env'
with open(env_path) as f:
    for line in f:
        if '=' in line:
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

import tushare as ts
ts.set_token(os.environ['TUSHARE_TOKEN'])
pro = ts.pro_api()
print("tushare连接成功")


def api(func, **kwargs):
    for i in range(3):
        try:
            r = func(**kwargs)
            time.sleep(0.35)
            return r
        except Exception as e:
            if i < 2:
                time.sleep(2)
            else:
                raise


def get_nearest_td(target):
    df = api(pro.trade_cal, exchange='SSE',
             start_date=str(int(target)-10), end_date=target)
    df = df[df['is_open']==1].sort_values('cal_date')
    return df.iloc[-1]['cal_date'] if not df.empty else target


# ============================================================
# Step 1: 获取多月截面数据用于计算因子
# 选择6个时间点（每半年一个），计算5因子截面
# ============================================================

def build_factor_cross_section(trade_date):
    """构建单月截面的5因子数据"""
    td = get_nearest_td(trade_date)

    # 基础行情数据
    df = api(pro.daily_basic, trade_date=td,
             fields='ts_code,pe_ttm,pb,total_mv,turnover_rate,close')
    if df is None or df.empty:
        return None

    # EP因子
    df['EP'] = 1.0 / df['pe_ttm']
    df.loc[df['pe_ttm'] <= 0, 'EP'] = np.nan
    df['EP'] = df['EP'].clip(-0.5, 0.5)

    # SIZE因子（小市值方向为正）
    df['SIZE'] = -np.log(df['total_mv'].clip(lower=1))

    # 低波动代理（用换手率的负数——低换手≈低波动）
    df['LOW_VOL'] = -df['turnover_rate']

    # 动量因子：需要12个月前的价格
    td_12ago = get_nearest_td(str(int(td) - 10100))  # 约1年前
    td_1ago = get_nearest_td(str(int(td) - 100))     # 约1个月前

    df_12 = api(pro.daily_basic, trade_date=td_12ago, fields='ts_code,close')
    df_1 = api(pro.daily_basic, trade_date=td_1ago, fields='ts_code,close')

    if df_12 is not None and df_1 is not None:
        df_mom = df_12.merge(df_1, on='ts_code', suffixes=('_12', '_1'))
        df_mom['MOM'] = df_mom['close_1'] / df_mom['close_12'] - 1
        df = df.merge(df_mom[['ts_code', 'MOM']], on='ts_code', how='left')
    else:
        df['MOM'] = np.nan

    # ROE因子：用 income + balancesheet 间接算
    # 简化方案：用 PB/PE 的倒数近似 ROE = E/B = (E/P)/(B/P) = EP/BP
    # ROE ≈ EP * PB = (1/PE) * PB
    df['QUALITY'] = (1.0 / df['pe_ttm'].clip(lower=1)) * df['pb'].clip(lower=0.1)
    df.loc[df['pe_ttm'] <= 0, 'QUALITY'] = np.nan

    # 下月收益（用于计算因子溢价）
    td_next = get_nearest_td(str(int(td) + 100))  # 约1个月后
    df_next = api(pro.daily_basic, trade_date=td_next, fields='ts_code,close')
    df_adj_now = api(pro.adj_factor, trade_date=td, fields='ts_code,adj_factor')
    df_adj_next = api(pro.adj_factor, trade_date=td_next, fields='ts_code,adj_factor')

    if df_next is not None and df_adj_now is not None and df_adj_next is not None:
        df_now_p = df[['ts_code', 'close']].merge(df_adj_now, on='ts_code')
        df_now_p['close_adj'] = df_now_p['close'] * df_now_p['adj_factor']

        df_next_p = df_next.merge(df_adj_next, on='ts_code')
        df_next_p['close_adj'] = df_next_p['close'] * df_next_p['adj_factor']

        df_ret = df_now_p[['ts_code', 'close_adj']].merge(
            df_next_p[['ts_code', 'close_adj']], on='ts_code', suffixes=('_now', '_next'))
        df_ret['ret_next'] = df_ret['close_adj_next'] / df_ret['close_adj_now'] - 1
        df = df.merge(df_ret[['ts_code', 'ret_next']], on='ts_code', how='left')
    else:
        df['ret_next'] = np.nan

    return df[['ts_code', 'EP', 'MOM', 'QUALITY', 'SIZE', 'LOW_VOL', 'ret_next']].dropna()


# ============================================================
# Step 2: 收集多月数据
# ============================================================

print("\n获取多月截面数据...")
# 取2022-2024年共6个时间点
dates = ['20220131', '20220630', '20221230', '20230630', '20231229', '20240628']

all_corrs = []
factor_returns = {f: [] for f in ['EP', 'MOM', 'QUALITY', 'SIZE', 'LOW_VOL']}

for dt in dates:
    print(f"\n  处理 {dt}...")
    df = build_factor_cross_section(dt)
    if df is None or len(df) < 200:
        print(f"    数据不足({len(df) if df is not None else 0}只)，跳过")
        continue

    print(f"    有效股票: {len(df)}")

    # 标准化因子
    factors = ['EP', 'MOM', 'QUALITY', 'SIZE', 'LOW_VOL']
    for f in factors:
        df[f] = (df[f] - df[f].mean()) / df[f].std()

    # 因子相关性
    corr = df[factors].corr()
    all_corrs.append(corr)

    # 因子收益率：分5层多空
    for f in factors:
        df['grp'] = pd.qcut(df[f], 5, labels=False, duplicates='drop')
        top = df[df['grp'] == 4]['ret_next'].mean()
        bot = df[df['grp'] == 0]['ret_next'].mean()
        factor_returns[f].append(top - bot)

# ============================================================
# Step 3: 汇总结果
# ============================================================

print("\n" + "="*60)
print("核实5结果：五大因子相关性矩阵（2022-2024均值）")
print("="*60)

if all_corrs:
    avg_corr = sum(all_corrs) / len(all_corrs)
    print(avg_corr.round(3).to_string())

    print("\n与书中对比：")
    print(f"  EP-MOM:      书中-0.15, 实测{avg_corr.loc['EP','MOM']:.3f}")
    print(f"  QUALITY-SIZE: 书中-0.30, 实测{avg_corr.loc['QUALITY','SIZE']:.3f}")
    print(f"  MOM-LOW_VOL: 书中-0.20, 实测{avg_corr.loc['MOM','LOW_VOL']:.3f}")
    print(f"  EP-LOW_VOL:  书中0.25, 实测{avg_corr.loc['EP','LOW_VOL']:.3f}")

print("\n" + "="*60)
print("核实6结果：各因子月度多空收益（2022-2024）")
print("="*60)

results_6 = {}
for f in ['EP', 'MOM', 'QUALITY', 'SIZE', 'LOW_VOL']:
    rets = factor_returns[f]
    if rets:
        arr = np.array(rets)
        ann_ret = np.mean(arr) * 12 * 100
        ann_vol = np.std(arr) * np.sqrt(12) * 100
        sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
        print(f"  {f:10s}: 月均={np.mean(arr)*100:.2f}%, 年化={ann_ret:.1f}%, 年化波动={ann_vol:.1f}%, 夏普={sharpe:.2f}")
        results_6[f] = {'annual_ret': ann_ret, 'annual_vol': ann_vol, 'sharpe': sharpe}

# 保存
output = {
    'correlations': avg_corr.to_dict() if all_corrs else {},
    'factor_returns': results_6,
    'note': '基于2022-2024年6个月度截面的全A股数据。QUALITY用EP*PB近似ROE。LOW_VOL用换手率负数近似。'
}
with open('book/code/verify_factors_result.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

print("\n结果已保存到 book/code/verify_factors_result.json")
