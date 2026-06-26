# -*- coding: utf-8 -*-
"""Fix ch05 post-5.5.2: add 'why' explanations, reduce dashes."""
filepath = "book/part2-理论篇/ch05-因子检验方法论.md"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

count = 0

# 1. 5.5.4: Add intuition for E[max epsilon] formula
old1 = '当 $\\epsilon_m \\sim N(0, \\sigma^2)$ 独立时，$E[\\max_m \\epsilon_m] \\approx \\sigma \\sqrt{2\\ln M}$'
new1 = '当 $\\epsilon_m \\sim N(0, \\sigma^2)$ 独立时，极值理论告诉我们：$M$个独立正态随机变量中最大值的数学期望约为 $\\sigma \\sqrt{2\\ln M}$。直觉上，$M$越大，"最幸运的那个"就越大，但增长速度是对数级的（翻倍$M$只让偏差增加约40%）'
if old1 in content:
    content = content.replace(old1, new1, 1); count += 1

# 2. 5.6.1: Add why AR(1)
old2 = '**AR(1)模型**：\n\n$IC_t = c + \\phi \\cdot IC_{t-1} + \\eta_t, \\quad \\phi \\in (0,1) \\tag{5.28}$'
new2 = '为什么用AR(1)来描述IC的时间动态？因为它是最简单的能捕捉"惯性"的模型。它只有一个核心参数$\\phi$就能表达"上月IC对本月IC的影响程度"，且实证中A股因子IC的自相关结构确实近似一阶衰减（二阶以上贡献很小）。\n\n**AR(1)模型**：\n\n$IC_t = c + \\phi \\cdot IC_{t-1} + \\eta_t, \\quad \\phi \\in (0,1) \\tag{5.28}$'
if old2 in content:
    content = content.replace(old2, new2, 1); count += 1

# 3. 5.6.3: Add why linear model for crowding
old3 = '设追逐某因子的总资金量为 $C_t$，因子溢价为 $\\lambda_t$。更多资金追逐→更多买卖→价差被压缩：\n\n$\\lambda_t = \\lambda_0 - \\gamma \\cdot C_t \\tag{5.30}$'
new3 = '为什么溢价和追逐资金量大致成线性关系？因为因子收益的本质是"被低估的股票涨回合理价格"。买入这些股票的资金越多，股价被推高得越快，"低估"的幅度就越小，剩余溢价也就越少。这里的线性假设是一个简化，但足以捕捉"资金越多则溢价越小"的核心规律。\n\n设追逐某因子的总资金量为 $C_t$，因子溢价为 $\\lambda_t$：\n\n$\\lambda_t = \\lambda_0 - \\gamma \\cdot C_t \\tag{5.30}$'
if old3 in content:
    content = content.replace(old3, new3, 1); count += 1

# 4. Replace excessive dashes in post-5.5.2 content
# Find dashes that should be natural language transitions
dash_fixes = [
    ('IC极其持久——如果本月IC高', 'IC极其持久，如果本月IC高'),
    ('IC几乎不可预测——每月', 'IC几乎不可预测，每月'),
    ('因子的"拥挤度指标"（如因子组合持仓的集中度）上升', '因子的"拥挤度指标"（如因子组合持仓的集中度）上升'),  # this one is fine
    ('时灵时不灵"，后者"稳如老狗"。', '时灵时不灵"，而后者则"稳如老狗"。'),
]
for old, new in dash_fixes:
    if old in content and old != new:
        content = content.replace(old, new, 1)
        count += 1

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"ch05 post-5.5.2: {count} fixes applied")
