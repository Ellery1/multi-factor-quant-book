# -*- coding: utf-8 -*-
filepath = "book/part2-理论篇/ch05-因子检验方法论.md"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = '**Newey-West 估计量**：\n\n$$\\widehat{\\text{Var}}_{NW}(\\hat{\\lambda})'
new = '''> **我们要解决的问题**：前面证明了"天真标准误"会低估不确定性（因为忽略了因子收益率的惯性）。那正确的标准误应该怎么算？
>
> **思路**：既然误差来源是"相邻月份的$\\hat{\\beta}_t$不独立"，那我们就把这种"不独立"的程度（即自协方差$\\gamma_1, \\gamma_2, ...$）**也算进方差里去**。具体做法是：真实方差 = 自身方差 + 所有相邻期的自协方差贡献之和。但离得越远的月份影响越小，所以给远期自协方差一个递减的权重（这就是Bartlett核的作用——像一个逐渐衰减的窗口）。
>
> **类比**：就像计算你通勤时间的"平均波动"——如果周一堵车，周二大概率也堵（自相关），你不能天真地把5天的通勤时间当作5个独立样本。正确做法是把"周一堵则周二也堵"这种关联也纳入波动的计算。

**Newey-West 估计量**：

$$\\widehat{\\text{Var}}_{NW}(\\hat{\\lambda})'''

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK")
else:
    print("MISS")
    idx = content.find('Newey-West 估计量')
    if idx > 0:
        print(repr(content[idx:idx+80]))
