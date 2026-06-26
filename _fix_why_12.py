# -*- coding: utf-8 -*-
"""Add 'why' explanations for ch03 formula 3.6 and ch05 formula 5.6."""

# Fix 1: ch03 §3.2.3 OLS matrix form
filepath = "book/part2-理论篇/ch03-因子的本质.md"
with open(filepath, 'r', encoding='utf-8') as f:
    c = f.read()

old1 = '$$\\hat{\\boldsymbol{\\beta}} = (\\mathbf{F}^T \\mathbf{F})^{-1} \\mathbf{F}^T \\mathbf{r} \\tag{3.6}$$\n\n这个公式是线性代数中"最小二乘解"的标准形式。'
new1 = '''$$\\hat{\\boldsymbol{\\beta}} = (\\mathbf{F}^T \\mathbf{F})^{-1} \\mathbf{F}^T \\mathbf{r} \\tag{3.6}$$

> 为什么最小二乘的解长这样？直觉上，$\\mathbf{F}^T\\mathbf{r}$ 计算的是"每个因子和收益的协方差"（信号强度），而 $(\\mathbf{F}^T\\mathbf{F})^{-1}$ 做的是"去除因子间的重叠后归一化"（避免重复计算）。两者相乘，就得到了"在考虑因子间相关性后，每个因子独立贡献了多少收益"。这和单因子情形下$\\beta = \\text{Cov}(f,r)/\\text{Var}(f)$是同一个思想的多维推广。

这个公式是线性代数中"最小二乘解"的标准形式。'''
if old1 in c:
    c = c.replace(old1, new1, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(c)
    print("  OK: ch03 formula 3.6 why")
else:
    print("  MISS: ch03 formula 3.6")

# Fix 2: ch05 §5.2.3 Grinold sqrt(BR)
filepath2 = "book/part2-理论篇/ch05-因子检验方法论.md"
with open(filepath2, 'r', encoding='utf-8') as f:
    c2 = f.read()

old2 = '$$\\text{策略夏普比} \\approx IC \\cdot \\sqrt{BR} \\tag{5.6}$$'
new2 = '''$$\\text{策略夏普比} \\approx IC \\cdot \\sqrt{BR} \\tag{5.6}$$

> 为什么是$\\sqrt{BR}$而不是$BR$？因为夏普比的分母是波动率（标准差），而$BR$个独立决策的组合波动率按$\\sqrt{BR}$缩小（即方差按$BR$缩小，标准差按$\\sqrt{BR}$缩小）。所以收益按$BR$线性增长、波动按$\\sqrt{BR}$增长，两者相除得到夏普比按$\\sqrt{BR}$增长。这和"分散投资降低风险"是同一个道理。'''
if old2 in c2:
    c2 = c2.replace(old2, new2, 1)
    with open(filepath2, 'w', encoding='utf-8') as f:
        f.write(c2)
    print("  OK: ch05 formula 5.6 why sqrt")
else:
    print("  MISS: ch05 formula 5.6")
