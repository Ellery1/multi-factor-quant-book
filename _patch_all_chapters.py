# -*- coding: utf-8 -*-
"""Apply all reasonable fixes from deepseek's round 2 review."""
import os

def patch_file(filepath, patches):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    count = 0
    for old, new in patches:
        if old in content:
            content = content.replace(old, new, 1)
            count += 1
        else:
            print(f"  MISS in {os.path.basename(filepath)}: {old[:50]}...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return count

total = 0

# ============================================================
# CH03 PATCHES
# ============================================================
ch03 = "book/part2-理论篇/ch03-因子的本质.md"

ch03_patches = [
    # 1.6: 多空组合推导中N的出现缺解释
    (
        '由于 $\\tilde{f}$ 已标准化（均值0），这恰好是 $N \\cdot \\text{Cov}(\\tilde{f}_t, r_{t+1})$。',
        '由于 $\\tilde{f}$ 已标准化（均值0），这恰好是 $N \\cdot \\text{Cov}(\\tilde{f}_t, r_{t+1})$（因为样本协方差 $\\text{Cov}(\\tilde{f}, r) = \\frac{1}{N}\\sum_i \\tilde{f}_i \\cdot r_i - \\bar{\\tilde{f}}\\cdot\\bar{r}$，而 $\\bar{\\tilde{f}}=0$，所以 $\\sum_i \\tilde{f}_i \\cdot r_i = N \\cdot \\text{Cov}(\\tilde{f}, r)$）。'
    ),
    # 3.1: 公式(3.14)多个符号未定义
    (
        '任何一只股票的收益都可以分解为：市场整体表现 + 风格因子暴露带来的收益 + 行业因子带来的收益 + Alpha + 无法解释的随机部分。',
        '各符号含义：\n' +
        '- $\\alpha_t$：截距，代表该期市场整体的平均收益水平\n' +
        '- $\\beta_{ik}$：股票$i$在第$k$个风格因子上的暴露程度（如对价值因子的敏感度）\n' +
        '- $f_{k,t}$：第$k$个风格因子在时刻$t$的因子收益率\n' +
        '- $\\gamma_{ij}$：行业归属哑变量（股票$i$属于行业$j$则为1，否则为0）\n' +
        '- $I_{ij}$：行业$j$的因子收益率\n' +
        '- $\\delta_i$：股票$i$对Alpha因子的暴露系数\n' +
        '- $g_{i,t}$：Alpha因子在时刻$t$的值（如某另类数据信号）\n' +
        '- $\\epsilon_{i,t+1}$：无法被任何已知因子解释的随机噪声\n\n' +
        '任何一只股票的收益都可以分解为：市场整体表现 + 风格因子暴露带来的收益 + 行业因子带来的收益 + Alpha + 无法解释的随机部分。'
    ),
]

n = patch_file(ch03, ch03_patches)
print(f"ch03: {n}/{len(ch03_patches)} applied")
total += n

# ============================================================
# CH04 PATCHES
# ============================================================
ch04 = "book/part2-理论篇/ch04-常见因子详解.md"

ch04_patches = [
    # 1.1: 动量12-1定义不一致 - 修改文字描述
    (
        '最常用的参数是 $J = 11$（即过去12个月的收益，跳过最近1个月），这就是经典的"12-1动量"。',
        '最常用的参数是 $J = 11$（即从$t-12$到$t-1$共11个月的累计收益，不含当月），这就是经典的"12-1动量"（"12"指回看起点在12个月前，"1"指跳过最近1个月）。'
    ),
    # 1.5: 低波动异象表述不精确
    (
        '**经验规律**：低波动率股票的长期收益反而**高于**高波动率股票——这与"高风险高收益"的教科书说法直接矛盾。',
        '**经验规律**：在控制了市场beta之后，低波动率股票的长期收益反而**高于**高波动率股票——表现为证券市场线（beta-收益关系）比CAPM预测的更"平"：高波动股票的实际收益低于CAPM预测值，低波动股票的实际收益高于CAPM预测值。这与"高风险必然带来高收益"的教科书简化说法相矛盾。'
    ),
]

n = patch_file(ch04, ch04_patches)
print(f"ch04: {n}/{len(ch04_patches)} applied")
total += n

# ============================================================
# CH05 PATCHES
# ============================================================
ch05 = "book/part2-理论篇/ch05-因子检验方法论.md"

ch05_patches = []

# Check if ch05 has the problematic formulas
with open(ch05, 'r', encoding='utf-8') as f:
    ch05_content = f.read()

# 1.2: N vs BR in Grinold formula
if 'IC \\cdot \\sqrt{N}' in ch05_content or 'IC × √N' in ch05_content or 'IC \\cdot \\sqrt N' in ch05_content:
    # Try various forms
    for pattern in ['$IC \\cdot \\sqrt{N}$', 'IC × √N', 'IC \\times \\sqrt{N}']:
        if pattern in ch05_content:
            print(f"  Found Grinold pattern: {pattern}")
            break

# Search for the actual text
if '策略夏普比' in ch05_content and '\\sqrt{N}' in ch05_content:
    ch05_patches.append((
        '$$\\text{策略夏普比} \\approx IC \\cdot \\sqrt{N}',
        '$$\\text{策略夏普比} \\approx IC \\cdot \\sqrt{BR}'
    ))
    # Also fix the explanation of N
    if '每期可选股票数量（广度）' in ch05_content:
        ch05_patches.append((
            '每期可选股票数量（广度）',
            '有效独立决策次数（广度，Breadth）。注意：$BR$不等于股票数量$N$——当股票间收益率有相关性时，$BR < N$。例如若3000只股票残差两两相关0.3，有效广度仅约$3000/(1+2999\\times0.3) \\approx 3.3$'
        ))

if ch05_patches:
    n = patch_file(ch05, ch05_patches)
    print(f"ch05: {n}/{len(ch05_patches)} applied")
    total += n
else:
    print("ch05: searching for alternative patterns...")
    # Try to find what's actually there
    idx = ch05_content.find('Grinold')
    if idx > 0:
        print(f"  Found 'Grinold' at pos {idx}: {ch05_content[idx:idx+100]}")
    idx2 = ch05_content.find('sqrt')
    if idx2 > 0:
        print(f"  Found 'sqrt' at pos {idx2}: {ch05_content[idx2:idx2+60]}")

# ============================================================
# CH06 PATCHES  
# ============================================================
ch06 = "book/part2-理论篇/ch06-因子合成与加权.md"

with open(ch06, 'r', encoding='utf-8') as f:
    ch06_content = f.read()

ch06_patches = []

# 2.4: VIF formula needs pre-explanation
if '方差膨胀因子' in ch06_content:
    vif_target = '方差膨胀因子（VIF'
    if vif_target in ch06_content:
        ch06_patches.append((
            vif_target,
            '> 当因子之间高度相关时，回归系数的估计变得极不稳定——某个因子的权重可能从+50%跳到-30%，仅仅因为输入数据稍有变化。**方差膨胀因子（VIF）** 量化了这种"不稳定程度"：VIF越大，说明这个因子与其他因子越"重复"，其系数估计越不可靠。一般认为VIF>10就该警惕了。\n\n方差膨胀因子（VIF'
        ))

if ch06_patches:
    n = patch_file(ch06, ch06_patches)
    print(f"ch06: {n}/{len(ch06_patches)} applied")
    total += n
else:
    print("ch06: no patches matched")

print(f"\n=== TOTAL: {total} patches applied across all chapters ===")
