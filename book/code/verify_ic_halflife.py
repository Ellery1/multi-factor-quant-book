# -*- coding: utf-8 -*-
"""
核实8: ch05 §5.6.2 五大因子IC半衰期
方法：每月计算各因子的Spearman Rank IC，对IC序列拟合AR(1)，算出φ和半衰期
时间段：2018-2024（约72个月，避免2015极端行情）
因子：EP, 动量(12-1), ROE(近似), 市值(负对数), 低波动(负换手率)
"""
import os, time, json
import numpy as np
import pandas as pd
from scipy import stats
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


def compute_monthly_ic(trade_date):
    """计算单月的5因子Spearman IC"""
    td = get_nearest_td(trade_date)
    
    # 下个月末
    year, month = int(td[:4]), int(td[4:6])
    if month == 12:
        next_month_end = f"{year+1}0131"
    else:
        next_month_end = f"{year}{month+1:02d}28"
    td_next = get_nearest_td(next_month_end)
    
    # 获取当月末数据
    df = api(pro.daily_basic, trade_date=td,
             fields='ts_code,pe_ttm,pb,total_mv,turnover_rate,close')
    if df is None or df.empty:
        return None
    
    # EP因子
    df['EP'] = 1.0 / df['pe_ttm'].clip(lower=1)
    df.loc[df['pe_ttm'] <= 0, 'EP'] = np.nan
    
    # SIZE因子（小市值方向为正）
    df['SIZE'] = -np.log(df['total_mv'].clip(lower=1))
    
    # 低波动代理（低换手=低波动方向为正）
    df['LOW_VOL'] = -df['turnover_rate']
    
    # ROE近似 = EP * PB = (1/PE) * PB
    df['QUALITY'] = df['EP'] * df['pb'].clip(lower=0.1)
    
    # 动量：需要12个月前价格
    td_12ago = get_nearest_td(str(int(td[:4])-1) + td[4:])  # 去年同月
    td_1ago = get_nearest_td(str(int(td[:4])) + f"{max(1,int(td[4:6])-1):02d}" + td[6:])
    
    df_12 = api(pro.daily_basic, trade_date=td_12ago, fields='ts_code,close')
    df_1 = api(pro.daily_basic, trade_date=td_1ago, fields='ts_code,close')
    
    if df_12 is not None and df_1 is not None and not df_12.empty and not df_1.empty:
        df_mom = df_12.merge(df_1, on='ts_code', suffixes=('_12','_1'))
        df_mom['MOM'] = df_mom['close_1'] / df_mom['close_12'] - 1
        df = df.merge(df_mom[['ts_code','MOM']], on='ts_code', how='left')
    else:
        df['MOM'] = np.nan
    
    # 获取下月收益
    df_now_close = api(pro.daily_basic, trade_date=td, fields='ts_code,close')
    df_next_close = api(pro.daily_basic, trade_date=td_next, fields='ts_code,close')
    adj_now = api(pro.adj_factor, trade_date=td, fields='ts_code,adj_factor')
    adj_next = api(pro.adj_factor, trade_date=td_next, fields='ts_code,adj_factor')
    
    if any(d is None or d.empty for d in [df_now_close, df_next_close, adj_now, adj_next]):
        return None
    
    df_p = df_now_close.merge(adj_now, on='ts_code')
    df_p['adj_close'] = df_p['close'] * df_p['adj_factor']
    df_n = df_next_close.merge(adj_next, on='ts_code')
    df_n['adj_close'] = df_n['close'] * df_n['adj_factor']
    
    df_ret = df_p[['ts_code','adj_close']].merge(df_n[['ts_code','adj_close']], on='ts_code', suffixes=('_now','_next'))
    df_ret['ret_next'] = df_ret['adj_close_next'] / df_ret['adj_close_now'] - 1
    
    df = df.merge(df_ret[['ts_code','ret_next']], on='ts_code', how='left')
    
    # 计算各因子的Spearman IC
    factors = ['EP', 'MOM', 'QUALITY', 'SIZE', 'LOW_VOL']
    ics = {}
    for f_name in factors:
        valid = df[[f_name, 'ret_next']].dropna()
        if len(valid) < 100:
            ics[f_name] = np.nan
        else:
            ic, _ = stats.spearmanr(valid[f_name], valid['ret_next'])
            ics[f_name] = ic
    
    return ics


# ============================================================
# 主程序：逐月计算IC
# ============================================================
print("开始逐月计算IC序列...")
print("时间段：2018.06 - 2024.06（每月一个截面，共约72个月）\n")

# 生成月末日期列表
month_ends = []
for year in range(2018, 2025):
    for month in range(1, 13):
        if year == 2024 and month > 6:
            break
        if year == 2018 and month < 6:
            continue
        month_ends.append(f"{year}{month:02d}28")

all_ics = []
for i, dt in enumerate(month_ends):
    print(f"  [{i+1}/{len(month_ends)}] {dt}...", end=' ')
    try:
        ics = compute_monthly_ic(dt)
        if ics:
            ics['date'] = dt
            all_ics.append(ics)
            print(f"EP={ics.get('EP',0):.3f} MOM={ics.get('MOM',0):.3f}")
        else:
            print("数据不全，跳过")
    except Exception as e:
        print(f"错误: {e}")

# ============================================================
# 拟合AR(1)并计算半衰期
# ============================================================
print("\n" + "="*60)
print("AR(1) 拟合结果")
print("="*60)

df_ics = pd.DataFrame(all_ics)
results = {}

factors = ['EP', 'MOM', 'QUALITY', 'SIZE', 'LOW_VOL']
factor_names = {'EP': 'EP（价值）', 'MOM': '12-1动量', 'QUALITY': 'ROE（质量）', 
                'SIZE': '市值（规模）', 'LOW_VOL': '波动率'}

for f_name in factors:
    ic_series = df_ics[f_name].dropna().values
    if len(ic_series) < 20:
        print(f"  {factor_names[f_name]}: 数据不足({len(ic_series)}个月)")
        continue
    
    # AR(1)拟合：IC_t = c + phi * IC_{t-1} + eta
    y = ic_series[1:]
    x = ic_series[:-1]
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    phi = slope
    c = intercept
    mu = c / (1 - phi) if abs(phi) < 1 else np.nan
    half_life = -np.log(2) / np.log(abs(phi)) if 0 < abs(phi) < 1 else np.inf
    
    results[f_name] = {
        'phi': phi,
        'half_life_months': half_life,
        'ic_mean': np.mean(ic_series),
        'ic_std': np.std(ic_series),
        'n_months': len(ic_series),
        'ar1_r2': r_value**2,
    }
    
    print(f"  {factor_names[f_name]:12s}: φ={phi:.3f}, 半衰期={half_life:.1f}月, IC均值={np.mean(ic_series):.4f}, n={len(ic_series)}月")

# 对比书中数据
print("\n" + "="*60)
print("与书中数据对比")
print("="*60)
book_values = {'EP': 0.85, 'MOM': 0.70, 'QUALITY': 0.88, 'SIZE': 0.92, 'LOW_VOL': 0.75}
for f_name in factors:
    if f_name in results:
        actual = results[f_name]['phi']
        book = book_values[f_name]
        diff = actual - book
        print(f"  {factor_names[f_name]:12s}: 书中φ={book:.2f}, 实测φ={actual:.3f}, 偏差={diff:+.3f}")

# 保存结果
output = {
    'results': results,
    'book_values': book_values,
    'note': '基于tushare全A股2018.06-2024.06月度Spearman IC序列拟合AR(1)。QUALITY用EP*PB近似ROE。LOW_VOL用负换手率近似。',
    'raw_ic_series': df_ics.to_dict(orient='records')
}
with open('book/code/verify_ic_halflife_result.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

print(f"\n结果已保存到 book/code/verify_ic_halflife_result.json")
print(f"共处理 {len(all_ics)} 个月的数据")
