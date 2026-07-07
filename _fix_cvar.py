# -*- coding: utf-8 -*-
filepath = "book/part4-进阶篇/ch09-风险管理与归因.md"
with open(filepath, 'r', encoding='utf-8') as f:
    c = f.read()

old = '''**关键性质**：CVaR > VaR，且对厚尾分布更敏感，它是比VaR更好的极端风险度量。

**数值例子**：
- 95% VaR = 8.87%：95%的概率亏损不超过8.87%
- 95% CVaR = 12.3%：在那5%的极端情况中，平均亏损12.3%'''

new = '''**关键性质**：CVaR > VaR，且对厚尾分布更敏感，它是比VaR更好的极端风险度量。

**怎么算？方法一：正态假设下的解析公式**

如果收益率服从正态分布 $r \\sim N(\\mu, \\sigma^2)$，CVaR有封闭解：

$$\\text{CVaR}_\\alpha = -\\mu + \\sigma \\cdot \\frac{\\phi(z_\\alpha)}{1-\\alpha} \\tag{9.5}$$

参数说明：
- $\\phi(z_\\alpha)$：标准正态分布在 $z_\\alpha$ 处的概率密度函数值。$z_{0.95}=1.645$ 对应 $\\phi(1.645)=0.1031$
- $1-\\alpha$：尾部概率（5%）

代入前面的数字（$\\mu=1\\%$，$\\sigma=6\\%$，$\\alpha=0.95$）：

$$\\text{CVaR}_{95\\%} = -1\\% + 6\\% \\times \\frac{0.1031}{0.05} = -1\\% + 6\\% \\times 2.063 = 11.4\\%$$

即在最坏的5%情形中，平均月亏损约11.4%。对比VaR的8.87%，CVaR高出约2.5个百分点。

**怎么算？方法二：历史模拟法（更实用，不假设分布）**

1. 收集过去120个月的组合月收益率
2. 从小到大排序
3. VaR = 第6小的值的绝对值（120 x 5% = 6）
4. CVaR = 前6个最差月份的平均亏损

**Worked Example**：假设最差的6个月收益率为：-12.1%、-10.5%、-9.8%、-8.3%、-7.6%、-7.2%

- 95% VaR（历史法）= 7.2%（第6差的月份）
- 95% CVaR（历史法）= (12.1+10.5+9.8+8.3+7.6+7.2)/6 = 9.25%

CVaR比VaR高2个百分点，即"一旦突破VaR，实际损失平均还要再深2个点"。'''

if old in c:
    c = c.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(c)
    print("OK: CVaR calculation methods added to disk file")
else:
    print("MISS")
