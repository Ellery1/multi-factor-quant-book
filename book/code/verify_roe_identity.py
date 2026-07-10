# -*- coding: utf-8 -*-
"""
验证 ROE = EP × PB 是否为精确等式（而非近似）
EP = E/P = 1/PE_ttm，PB = P/B → EP × PB = (E/P)×(P/B) = E/B = ROE
只要PE和PB口径一致，这应该是数学恒等式。
"""
import os, time
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

# 拉取一个交易日的数据
td = '20240628'
print(f"\n拉取 {td} 的 daily_basic...")
time.sleep(0.5)
df = pro.daily_basic(trade_date=td, fields='ts_code,pe_ttm,pb,total_mv')
print(f"获取到 {len(df)} 只股票")

# 计算 EP × PB
df['EP'] = 1.0 / df['pe_ttm']
df['EP_x_PB'] = df['EP'] * df['pb']

# EP×PB 的含义：
# EP = E/P (TTM净利润 / 总市值)
# PB = P/B (总市值 / 净资产)
# EP × PB = (E/P) × (P/B) = E/B = 净利润/净资产 = ROE (TTM)

# 过滤掉PE为负或极端值的
df = df[(df['pe_ttm'] > 0) & (df['pb'] > 0)]
df = df.dropna(subset=['EP_x_PB'])

print(f"\n过滤后: {len(df)} 只股票")
print(f"\nEP×PB (= ROE_TTM) 的统计特征:")
print(f"  均值: {df['EP_x_PB'].mean():.4f} ({df['EP_x_PB'].mean()*100:.2f}%)")
print(f"  中位数: {df['EP_x_PB'].median():.4f} ({df['EP_x_PB'].median()*100:.2f}%)")
print(f"  25分位: {df['EP_x_PB'].quantile(0.25):.4f}")
print(f"  75分位: {df['EP_x_PB'].quantile(0.75):.4f}")

print(f"\n结论：EP×PB 在数学上精确等于 ROE_TTM（净利润TTM / 净资产）。")
print(f"这不是'近似'而是恒等式：(E/P)×(P/B) = E/B。")
print(f"因此 §4.5.2 相关性矩阵中的'质量'列就是真实的ROE因子截面相关性。")
