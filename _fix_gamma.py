# -*- coding: utf-8 -*-
filepath = "book/part2-理论篇/ch05-因子检验方法论.md"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = '**低估程度有多大？** 假设 $\\gamma_1 = 0.3\\gamma_0$，$\\gamma_2 = 0.1\\gamma_0$，其余≈0：'
new = '''**低估程度有多大？** 假设 $\\gamma_1 = 0.3\\gamma_0$，$\\gamma_2 = 0.1\\gamma_0$，其余≈0：

> **这个假设在说什么？** $\\gamma_0$ 是因子月度收益率 $\\hat{\\beta}_t$ 的方差（衡量"月与月之间波动多大"）。$\\gamma_1 = 0.3\\gamma_0$ 意思是：如果上个月因子收益率比均值高了1%，这个月你可以预期它仍然比均值高约0.3%——"惯性"保留了30%。$\\gamma_2 = 0.1\\gamma_0$ 意思是：两个月前的惯性到现在只剩10%，三个月后几乎消失。
>
> **为什么现实中确实如此？** 市场风格切换不是一天完成的。当价值股开始跑赢→更多基金经理被业绩压力驱动加仓价值股→价值股进一步跑赢→惯性持续一到三个月→直到估值差收窄或突发事件打破趋势。这种"风格动量"在A股实证中通常表现为：因子收益率的一阶自相关约0.2-0.4，二阶约0.05-0.15，三阶以上接近零。所以$\\gamma_1 = 0.3\\gamma_0$和$\\gamma_2 = 0.1\\gamma_0$是一个符合A股经验的典型假设。'''

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK")
else:
    print("MISS")
