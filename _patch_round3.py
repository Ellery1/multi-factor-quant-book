# -*- coding: utf-8 -*-
"""Round 3 patches."""
import os

def patch_file(filepath, patches):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    count = 0
    for name, old, new in patches:
        if old in content:
            content = content.replace(old, new, 1)
            count += 1
            print(f"  OK: {name}")
        else:
            print(f"  MISS: {name} -- {old[:50]}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return count

total = 0

# ============================================================
# CH03: Add parameter definitions for formula (3.14)
# ============================================================
ch03 = "book/part2-理论篇/ch03-因子的本质.md"
with open(ch03, 'r', encoding='utf-8') as f:
    c = f.read()

# Find the formula 3.14 area - look for the tag
idx = c.find('\\tag{3.14}')
if idx > 0:
    # Find the end of the formula line (next double newline after tag)
    end_formula = c.find('\n\n', idx)
    if end_formula > 0:
        # Check if parameter definitions already exist nearby
        next_200 = c[end_formula:end_formula+200]
        if '参数说明' not in next_200 and '$\\gamma_{ij}$' not in next_200:
            # Insert after the first paragraph following the formula
            # Find "任何一只股票" or similar
            marker = c.find('任何一只股票的收益', end_formula)
            if marker < 0:
                # Try deepseek's version
                marker = c.find('任意一只股票的收益', end_formula)
            if marker > 0:
                # Find end of that paragraph
                para_end = c.find('\n\n', marker)
                if para_end > 0:
                    insert_text = '\n\n参数说明：\n' + \
                        '- $r_{i,t+1}$（等式左边）：股票$i$在$t+1$期的收益率\n' + \
                        '- $\\alpha_t$：截距项，代表市场整体的平均收益水平\n' + \
                        '- $\\beta_{ik}$：股票$i$在第$k$个风格因子上的暴露度\n' + \
                        '- $f_{k,t}$：第$k$个风格因子在$t$期的收益率\n' + \
                        '- $\\gamma_{ij}$：行业归属哑变量（股票$i$属于行业$j$则=1，否则=0）\n' + \
                        '- $I_{ij}$：行业$j$的因子收益率\n' + \
                        '- $\\delta_i$：股票$i$对Alpha因子的暴露系数\n' + \
                        '- $g_{i,t}$：Alpha因子在$t$期的值\n' + \
                        '- $\\epsilon_{i,t+1}$：随机扰动项（个股特异风险）'
                    c = c[:para_end] + insert_text + c[para_end:]
                    print("  OK: ch03 formula 3.14 params")
                    total += 1
                else:
                    print("  MISS: ch03 3.14 - can't find para end")
            else:
                print("  MISS: ch03 3.14 - can't find '任何/任意一只股票'")
        else:
            print("  SKIP: ch03 3.14 params already exist")
    else:
        print("  MISS: ch03 3.14 - can't find end of formula")
else:
    print("  MISS: ch03 - tag 3.14 not found")

# CH03: Add BAB citation in 3.3.3
bab_old = '这就是"Betting Against Beta"因子'
bab_new = '这就是"Betting Against Beta"因子（Frazzini, A. & Pedersen, L.H., "Betting Against Beta," *Journal of Financial Economics*, Vol.111, No.1, 2014, pp.1-25）'
if bab_old in c and 'Frazzini' not in c[c.find(bab_old):c.find(bab_old)+200]:
    c = c.replace(bab_old, bab_new, 1)
    print("  OK: ch03 BAB citation")
    total += 1
else:
    print("  SKIP: ch03 BAB (already cited or not found)")

with open(ch03, 'w', encoding='utf-8') as f:
    f.write(c)

# ============================================================
# CH05: Fix N/BR inconsistency completely
# ============================================================
ch05 = "book/part2-理论篇/ch05-因子检验方法论.md"
with open(ch05, 'r', encoding='utf-8') as f:
    c = f.read()

ch05_count = 0

# Fix the explanation text after formula 5.6
old_n_explain = '每期可选股票数量'
if old_n_explain in c:
    # Check context
    idx = c.find(old_n_explain)
    context = c[max(0,idx-50):idx+100]
    if 'BR' not in context:  # hasn't been fixed yet
        # Replace with BR explanation
        c = c.replace(old_n_explain, '有效独立决策次数', 1)
        ch05_count += 1
        print("  OK: ch05 N->BR explanation")

# Fix formula 5.7 if it still uses sqrt{N}
if '\\sqrt{N} \\cdot f(\\text{' in c:
    c = c.replace(
        '\\sqrt{N} \\cdot f(\\text{相关结构})',
        '\\sqrt{BR}',
        1
    )
    ch05_count += 1
    print("  OK: ch05 formula 5.7 sqrt{N}*f -> sqrt{BR}")
elif '\\sqrt{N}' in c:
    # Check if there's still a stray sqrt{N} in the Grinold area
    grinold_idx = c.find('Grinold')
    if grinold_idx > 0:
        area = c[grinold_idx:grinold_idx+500]
        if '\\sqrt{N}' in area:
            print(f"  INFO: ch05 still has sqrt{{N}} near Grinold")

if ch05_count > 0:
    with open(ch05, 'w', encoding='utf-8') as f:
        f.write(c)
    total += ch05_count
    print(f"  ch05: {ch05_count} fixes")
else:
    print("  ch05: nothing to fix (may already be done)")

# ============================================================
# CH06: Fix VIF markdown format error
# ============================================================
ch06 = "book/part2-理论篇/ch06-因子合成与加权.md"
with open(ch06, 'r', encoding='utf-8') as f:
    c = f.read()

if '**> 当因子之间' in c:
    c = c.replace('**> 当因子之间', '> 当因子之间', 1)
    with open(ch06, 'w', encoding='utf-8') as f:
        f.write(c)
    print("  OK: ch06 VIF format fix")
    total += 1
else:
    print("  SKIP: ch06 VIF format (not found or already fixed)")

# ============================================================
# CH13: Add DSR complete citation
# ============================================================
ch13 = "book/part5-进阶篇/ch13-过拟合与陷阱.md"
with open(ch13, 'r', encoding='utf-8') as f:
    c = f.read()

if 'Bailey & Lopez de Prado (2014)' in c or 'Bailey & López de Prado (2014)' in c:
    # Check if citation already complete
    if 'Journal of Portfolio Management' not in c[c.find('Bailey'):c.find('Bailey')+300]:
        old_cite = 'Bailey & Lopez de Prado (2014)'
        if old_cite not in c:
            old_cite = 'Bailey & López de Prado (2014)'
        new_cite = old_cite + ' ("The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality," *Journal of Portfolio Management*, Vol.40, No.5, 2014, pp.94-107)'
        c = c.replace(old_cite, new_cite, 1)
        with open(ch13, 'w', encoding='utf-8') as f:
            f.write(c)
        print("  OK: ch13 DSR citation")
        total += 1
    else:
        print("  SKIP: ch13 DSR citation already complete")
else:
    print("  MISS: ch13 DSR citation - pattern not found")

# ============================================================
# CH14: Add Almgren-Chriss citation
# ============================================================
ch14 = "book/part5-进阶篇/ch14-从回测到实盘.md"
with open(ch14, 'r', encoding='utf-8') as f:
    c = f.read()

if 'Almgren' in c and 'Journal of Risk' not in c:
    almgren_idx = c.find('Almgren')
    # Find end of sentence
    sent_end = c.find('。', almgren_idx)
    if sent_end < 0:
        sent_end = c.find('\n', almgren_idx)
    # Insert citation after first mention
    old_almgren = c[almgren_idx:sent_end+1]
    new_almgren = old_almgren + '\n\n> 参考：Almgren, R. & Chriss, N. (2000). "Optimal Execution of Portfolio Transactions." *Journal of Risk*, Vol.3, No.2, pp.5-39.'
    c = c.replace(old_almgren, new_almgren, 1)
    with open(ch14, 'w', encoding='utf-8') as f:
        f.write(c)
    print("  OK: ch14 Almgren-Chriss citation")
    total += 1
elif 'Almgren' not in c:
    print("  SKIP: ch14 no Almgren reference found")
else:
    print("  SKIP: ch14 Almgren citation already complete")

print(f"\n=== TOTAL: {total} patches applied ===")
