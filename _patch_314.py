# -*- coding: utf-8 -*-
f = open('book/part2-理论篇/ch03-因子的本质.md', 'r', encoding='utf-8')
c = f.read()
f.close()

old = '\\tag{3.14}$$\n\n### 3.4.2'
new = '\\tag{3.14}$$\n\n' + \
    '参数说明：\n' + \
    '- $r_{i,t+1}$（等式左边）：股票$i$在$t+1$期的收益率\n' + \
    '- $\\alpha_t$：截距项，代表市场整体的平均收益水平\n' + \
    '- $\\beta_{ik}$：股票$i$在第$k$个风格因子上的暴露度\n' + \
    '- $f_{k,t}$：第$k$个风格因子在$t$期的收益率\n' + \
    '- $\\gamma_{ij}$：行业归属哑变量（股票$i$属于行业$j$则=1，否则=0）\n' + \
    '- $I_{ij}$：行业$j$的因子收益率\n' + \
    '- $\\delta_i$：股票$i$对Alpha因子的暴露系数\n' + \
    '- $g_{i,t}$：Alpha因子在$t$期的值\n' + \
    '- $\\epsilon_{i,t+1}$：随机扰动项（个股特异风险）\n\n' + \
    '### 3.4.2'

if old in c:
    c = c.replace(old, new, 1)
    f = open('book/part2-理论篇/ch03-因子的本质.md', 'w', encoding='utf-8')
    f.write(c)
    f.close()
    print("OK: ch03 formula 3.14 params inserted")
else:
    print("MISS")
