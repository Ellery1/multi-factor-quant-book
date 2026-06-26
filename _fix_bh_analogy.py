# -*- coding: utf-8 -*-
filepath = "book/part2-理论篇/ch05-因子检验方法论.md"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = '> **类比**：就像面试筛选。前几名候选人你用严格标准（p值要很小才通过），后面的候选人你标准逐渐放宽（位置越靠后允许p越大）。但如果某个候选人连放宽后的标准都达不到——从他开始往后全部淘汰。'

new = '> **类比**：想象你在审查一份按"嫌疑程度"排序的名单（p值最小的排最前，即"最可能有效"排最前）。对排名靠前的，你标准严格（p必须非常小才能"定罪"）；对排名靠后的，你逐渐放宽容忍度，因为排在后面本身就说明证据较弱。一旦某个位置的证据连放宽后的标准都达不到，那从这个位置往后全部判"证据不足"。'

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK: analogy fixed")
else:
    print("MISS")
