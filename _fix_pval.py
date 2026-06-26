# -*- coding: utf-8 -*-
filepath = "book/part2-理论篇/ch05-因子检验方法论.md"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = '假设你测试了10个因子候选，得到如下p值（已从小到大排序）：'
new = '''假设你测试了10个因子候选，对每个因子都做了§5.2.5的t检验，得到各自的p值（已从小到大排序）：

> 回顾：p值是"假设因子无效时，纯靠运气观察到当前结果（或更极端结果）的概率"。p越小，说明"纯属偶然"的解释越站不住脚，因子越可能真的有效。详见§5.1.1第四步。'''

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK")
else:
    print("MISS")
