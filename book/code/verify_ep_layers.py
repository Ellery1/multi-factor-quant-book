# -*- coding: utf-8 -*-
"""
核实7: ch05 §5.3.3 EP因子单调性检验 — 用真实A股数据
计算EP因子分5层的月均收益，并计算MR统计量
时间段：2020-2024（近5年）
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
print("tushare连接成功\n")


def api(func, **kwargs):
    for i in range(3):
        try:
            r = func(**kwargs)
            time.sleep(0.4)
            return r
        except Exception as e:
            if i < 2: time.sleep(2)
            else: raise


def get_nearest_td(target):
    df = api(pro.trade_cal, exchange='SSE',
             start_date=str(int(target)-10), end_date=target)
    df = df[df['is_open']==1].sort_values('cal_date')
    return df.iloc[-1]['cal_date'] if not df.empty else target


# 取每半年一个截面（节省API），计算EP分层的次月收益
# 选10个时间点覆盖2020-2024
sample_dates = [
    '20200630', '20201231',
    '20210630', '20211231',
    '20220630', '20221230',
    '20230630', '20231229',
    '20240329', '20240628',
]

all_group_returns = []  # 每个元素是一个dict: {G1:x, G2:x, G3:x, G4:x, G5:x}

for dt in sample_dates:
    td = get_nearest_td(dt)
    # 下个月末
    if dt.endswith('0630') or dt.endswith('0628') or dt.endswith('0329'):
        td_next = get_nearest_td(str(int(dt[:6]) + 1) + '28')
    else:
        # 12月末 → 次年1月末
        year = int(dt[:4])
        td_next = get_nearest_td(f'{year+1}0131')

    print(f"处理 {td} → {td_next}...")

    # 获取当月末PE
    df_pe = api(pro.daily_basic, trade_date=td, fields='ts_code,pe_ttm,close')
    if df_pe is None or df_pe.empty:
        print(f"  PE数据为空，跳过")
        continue

    # EP = 1/PE, 剔除PE≤0
    df_pe = df_pe[df_pe['pe_ttm'] > 0].copy()
    df_pe['EP'] = 1.0 / df_pe['pe_ttm']
    df_pe = df_pe[df_pe['EP'] < 1.0]  # 剔除极端值

    # 获取次月末收盘价和复权因子
    df_now = api(pro.daily_basic, trade_date=td, fields='ts_code,close')
    df_next = api(pro.daily_basic, trade_date=td_next, fields='ts_code,close')
    adj_now = api(pro.adj_factor, trade_date=td, fields='ts_code,adj_factor')
    adj_next = api(pro.adj_factor, trade_date=td_next, fields='ts_code,adj_factor')

    if any(d is None or d.empty for d in [df_now, df_next, adj_now, adj_next]):
        print(f"  价格/复权数据不全，跳过")
        continue

    # 计算复权收益
    df_p = df_now.merge(adj_now, on='ts_code')
    df_p['close_adj_now'] = df_p['close'] * df_p['adj_factor']
    df_n = df_next.merge(adj_next, on='ts_code')
    df_n['close_adj_next'] = df_n['close'] * df_n['adj_factor']

    df_ret = df_p[['ts_code', 'close_adj_now']].merge(
        df_n[['ts_code', 'close_adj_next']], on='ts_code')
    df_ret['ret'] = df_ret['close_adj_next'] / df_ret['close_adj_now'] - 1

    # 合并
    df = df_pe[['ts_code', 'EP']].merge(df_ret[['ts_code', 'ret']], on='ts_code')
    df = df.dropna()
    df = df[(df['ret'] > -0.5) & (df['ret'] < 1.0)]  # 剔除异常

    if len(df) < 500:
        print(f"  样本不足({len(df)})，跳过")
        continue

    # 分5组
    df['group'] = pd.qcut(df['EP'], 5, labels=['G1(低EP)', 'G2', 'G3', 'G4', 'G5(高EP)'])
    grp = df.groupby('group', observed=False)['ret'].mean() * 100

    result = grp.to_dict()
    all_group_returns.append(result)
    print(f"  n={len(df)}, G1={result['G1(低EP)']:.2f}% G5={result['G5(高EP)']:.2f}% 差={result['G5(高EP)']-result['G1(低EP)']:.2f}pp")


# 计算多期均值
print("\n" + "="*60)
print("EP因子5分层月均收益（2020-2024，10个半年度截面均值）")
print("="*60)

if all_group_returns:
    df_all = pd.DataFrame(all_group_returns)
    avg = df_all.mean()
    print(f"\n各组月均收益：")
    for g in ['G1(低EP)', 'G2', 'G3', 'G4', 'G5(高EP)']:
        print(f"  {g}: {avg[g]:.3f}%")

    # MR统计量
    groups = [avg['G1(低EP)'], avg['G2'], avg['G3'], avg['G4'], avg['G5(高EP)']]
    diffs = [groups[i] - groups[i+1] for i in range(4)]
    MR = max(diffs)
    print(f"\n相邻组差值: {[f'{d:.3f}' for d in diffs]}")
    print(f"MR = max(相邻组差值) = {MR:.3f}")
    print(f"MR {'< 0 → 严格单调 ✓' if MR < 0 else '>= 0 → 非严格单调 ✗'}")

    # 多空收益
    spread = avg['G5(高EP)'] - avg['G1(低EP)']
    print(f"\n多空月均收益(G5-G1): {spread:.3f}%")
    print(f"年化: {spread*12:.1f}%")

    # 保存
    output = {
        'avg_group_returns': avg.to_dict(),
        'MR': MR,
        'n_samples': len(all_group_returns),
        'spread_monthly': spread,
        'spread_annual': spread * 12,
        'all_samples': all_group_returns,
        'note': 'EP因子(1/PE_TTM)对全A股分5层，2020-2024年10个半年度截面的月均收益'
    }
    with open('book/code/verify_ep_layers_result.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    print("\n结果已保存到 book/code/verify_ep_layers_result.json")
else:
    print("无有效数据！")
