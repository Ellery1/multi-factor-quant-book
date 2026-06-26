# -*- coding: utf-8 -*-
filepath = "book/part2-理论篇/ch05-因子检验方法论.md"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: 导读框中的"期望会有5个"
content = content.replace(
    '测100个因子、用5%显著性水平，期望会有5个"假阳性"，说明纯随机因子也能通过检验。',
    '测100个因子、用5%显著性水平，数学期望上会产生5个"假阳性"（$100 \\times 5\\% = 5$），说明纯随机因子也能通过检验。'
)

# Fix 2: 正文中的"你期望发现几个"
content = content.replace(
    '如果这100个因子**全部无效**（全是噪声），你期望"发现"几个"显著"的？',
    '如果这100个因子**全部无效**（全是噪声），按照数学期望你会"发现"几个"显著"的？'
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("OK")
