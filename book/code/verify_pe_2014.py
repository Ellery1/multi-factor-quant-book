# -*- coding: utf-8 -*-
"""
核实1：ch03 §3.1.1 — PE分组效应（2014年）
验证：A股按PE分5组，低PE组是否收益最高

方法：
1. 取2013年末的PE_TTM数据（daily_basic接口）
2. 取2014年各股票的年度涨跌幅
3. 按PE分5组，计算各组的年度平均收益

数据源：tushare pro
"""

import os, time
import numpy as np
import pandas as pd
from pathlib import Path

# 加载token
env_path = Path(__file__).parent / '.env'
with open(env_path) as f:
    for line in f:
        if '=' in line:
            k, v = line.strip().split('=', 1)
            os.environ[k] = v

import tushare as ts
ts.set_token(os.environ['TUSHARE_TOKEN'])
pro = ts.pro_api()

def get_trade_date_near(target, direction='backward'):
    """获取最近的交易日"""
    df = pro.trade_cal(exchange='SSE', start_date=str(int(target)-5), end_date=str(int(target)+5))
    time.sleep(0.3)
    df = df[df['is_open'] == 1].sort_values('cal_date')
    if direction == 'backward':
        valid = df[df['cal_date'] <= target]
        return valid.iloc[-1]['cal_date'] if not valid.empty else target
    else:
        valid = df[df['cal_date'] >= target]
        return valid.iloc[0]['cal_date'] if not valid.empty else target


print("="*60)
print("核实1：PE分组效应（2014年）")
print("="*60)

# Step 1: 获取2013年最后一个交易日的PE数据
end_2013 = get_trade_date_near('20131231', 'backward')
print(f"2013年末交易日: {end_2013}")

df_pe = pro.daily_basic(trade_date=end_2013, fields='ts_code,pe_ttm,total_mv,turnover_rate')
time.sleep(0.5)
print(f"获取到 {len(df_pe)} 只股票的PE数据")

# 剔除PE≤0或异常大的
df_pe = df_pe[(df_pe['pe_ttm'] > 0) & (df_pe['pe_ttm'] < 500)].copy()
df_pe = df_pe.dropna(subset=['pe_ttm'])
print(f"有效样本（PE>0且<500）: {len(df_pe)} 只")

# Step 2: 获取2014年的年度涨跌幅
# 方法：获取2014年初和年末的收盘价（用daily_basic的close字段不含复权，改用stk_factor）
# 简化：用2014年12月末 / 2014年1月初的前复权价格

end_2014 = get_trade_date_near('20141231', 'backward')
start_2014 = get_trade_date_near('20140102', 'forward')
print(f"2014年首尾交易日: {start_2014} ~ {end_2014}")

# 获取年初和年末的前复权收盘价
# 使用 pro.daily 接口获取个股日线 — 但截面太大，改用 daily_basic 的 close
df_start = pro.daily_basic(trade_date=start_2014, fields='ts_code,close')
time.sleep(0.5)
df_end = pro.daily_basic(trade_date=end_2014, fields='ts_code,close')
time.sleep(0.5)

print(f"年初数据: {len(df_start)} 只, 年末数据: {len(df_end)} 只")

# 注意：daily_basic的close不含复权！需要用adj_factor调整
# 获取复权因子
df_adj_start = pro.adj_factor(trade_date=start_2014, fields='ts_code,adj_factor')
time.sleep(0.5)
df_adj_end = pro.adj_factor(trade_date=end_2014, fields='ts_code,adj_factor')
time.sleep(0.5)

# 计算前复权价格
df_start = df_start.merge(df_adj_start, on='ts_code')
df_start['close_adj'] = df_start['close'] * df_start['adj_factor']

df_end = df_end.merge(df_adj_end, on='ts_code')
df_end['close_adj'] = df_end['close'] * df_end['adj_factor']

# 合并计算年度收益
df_ret = df_start[['ts_code', 'close_adj']].merge(
    df_end[['ts_code', 'close_adj']], on='ts_code', suffixes=('_start', '_end')
)
df_ret['ret_2014'] = df_ret['close_adj_end'] / df_ret['close_adj_start'] - 1

# Step 3: 合并PE和收益
df = df_pe[['ts_code', 'pe_ttm']].merge(df_ret[['ts_code', 'ret_2014']], on='ts_code')
df = df.dropna()
# 剔除涨跌幅异常的（可能是停牌或数据错误）
df = df[(df['ret_2014'] > -0.9) & (df['ret_2014'] < 5.0)]
print(f"\n最终有效样本: {len(df)} 只股票")

# Step 4: 分5组
df['pe_group'] = pd.qcut(df['pe_ttm'], 5, labels=['G1(PE最低)', 'G2', 'G3', 'G4', 'G5(PE最高)'])

result = df.groupby('pe_group').agg(
    mean_ret=('ret_2014', lambda x: x.mean()*100),
    median_ret=('ret_2014', lambda x: x.median()*100),
    count=('ret_2014', 'count'),
    pe_range=('pe_ttm', lambda x: f"{x.min():.1f}~{x.max():.1f}")
).round(1)

print("\n" + "="*60)
print("结果：2014年A股PE分5组的年度收益")
print("="*60)
print(result.to_string())
print(f"\nG1(低PE) - G5(高PE) 均值收益差: {result.iloc[0]['mean_ret'] - result.iloc[-1]['mean_ret']:.1f}%")
print("\n书中声称: G1~+52%, G2~+38%, G3~+25%, G4~+18%, G5~+12%")
print("请对比实际结果判断是否需要修正。")

# 保存结果
result.to_csv('book/code/verify_pe_2014_result.csv', encoding='utf-8-sig')
print("\n结果已保存到 book/code/verify_pe_2014_result.csv")
