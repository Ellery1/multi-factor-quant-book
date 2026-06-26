# -*- coding: utf-8 -*-
"""Update build_book.py CHAPTERS config then run it to regenerate HTML."""
import re

filepath = "build_book.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the CHAPTERS definition with new structure
old_chapters_start = 'CHAPTERS = ['
old_chapters_end = ']\n\n\n# ======' # ends before next section

# Find the CHAPTERS block
start_idx = content.find(old_chapters_start)
# Find the closing of the CHAPTERS list (the ]\n before next section comment)
# Search for the pattern ]\n)\n]\n\n which marks end of CHAPTERS
end_pattern = '    ]),\n]\n'
end_idx = content.find(end_pattern, start_idx)
if end_idx > 0:
    end_idx += len(end_pattern)

new_chapters = '''CHAPTERS = [
    ("前言", [
        (os.path.join(BOOK_DIR, "README.md"),),
    ]),
    ("第一篇 · 认知篇", [
        (os.path.join(BOOK_DIR, "part1-认知篇", "ch01-什么是量化投资.md"),),
        (os.path.join(BOOK_DIR, "part1-认知篇", "ch02-多因子模型的前世今生.md"),),
    ]),
    ("第二篇 · 理论篇", [
        (os.path.join(BOOK_DIR, "part2-理论篇", "ch03-因子的本质.md"),),
        (os.path.join(BOOK_DIR, "part2-理论篇", "ch04-常见因子详解.md"),),
        (os.path.join(BOOK_DIR, "part2-理论篇", "ch05-因子检验方法论.md"),),
        (os.path.join(BOOK_DIR, "part2-理论篇", "ch06-因子合成与加权.md"),),
    ]),
    ("第三篇 · 工具与实践篇", [
        (os.path.join(BOOK_DIR, "part3-工具与实践篇", "ch07-数据获取与回测框架.md"),),
        (os.path.join(BOOK_DIR, "part3-工具与实践篇", "ch08-A股多因子策略实战.md"),),
    ]),
    ("第四篇 · 进阶篇", [
        (os.path.join(BOOK_DIR, "part4-进阶篇", "ch09-风险管理与归因.md"),),
        (os.path.join(BOOK_DIR, "part4-进阶篇", "ch10-过拟合与陷阱.md"),),
        (os.path.join(BOOK_DIR, "part4-进阶篇", "ch11-从回测到实盘.md"),),
        (os.path.join(BOOK_DIR, "part4-进阶篇", "ch12-前沿方向与延伸阅读.md"),),
    ]),
    ("附录", [
        (os.path.join(BOOK_DIR, "appendix", "appendix-a-python快速入门.md"),),
        (os.path.join(BOOK_DIR, "appendix", "appendix-b-数学回顾.md"),),
        (os.path.join(BOOK_DIR, "appendix", "appendix-c-数据源与工具清单.md"),),
        (os.path.join(BOOK_DIR, "appendix", "appendix-d-术语表.md"),),
    ]),
]
'''

if start_idx > 0 and end_idx > start_idx:
    content = content[:start_idx] + new_chapters + content[end_idx:]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"OK: Updated CHAPTERS config (pos {start_idx}-{end_idx})")
else:
    print(f"MISS: start={start_idx}, end={end_idx}")
