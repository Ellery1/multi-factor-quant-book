#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将多因子量化投资书籍的所有 Markdown 章节整合为一个精美的 HTML 页面。
"""

import os
import re
import markdown
from html import escape

BOOK_DIR = r"D:\project\gao7gao8\多因子量化的方法论简述\book"
OUTPUT_FILE = r"D:\project\gao7gao8\多因子量化的方法论简述\multi-factor-quant-book.html"

# ============================================================
# 章节定义：按书籍顺序
# ============================================================
CHAPTERS = [
    # (part_name, part_title, [(filename, chapter_title), ...])
    ("前言", [
        (os.path.join(BOOK_DIR, "README.md"), "前言：多因子量化投资——从理论到实践"),
    ]),
    ("第一篇 · 认知篇", [
        (os.path.join(BOOK_DIR, "part1-认知篇", "ch01-什么是量化投资.md"), "第1章：什么是量化投资——从主观到量化的思维转变"),
        (os.path.join(BOOK_DIR, "part1-认知篇", "ch02-多因子模型的前世今生.md"), "第2章：多因子模型的前世今生——从CAPM到多因子"),
    ]),
    ("第二篇 · 理论篇", [
        (os.path.join(BOOK_DIR, "part2-理论篇", "ch03-因子的本质.md"), "第3章：因子的本质——从直觉到严格定义"),
        (os.path.join(BOOK_DIR, "part2-理论篇", "ch04-常见因子详解.md"), "第4章：常见因子详解——经济逻辑与推导"),
        (os.path.join(BOOK_DIR, "part2-理论篇", "ch05-因子检验方法论.md"), "第5章：因子检验方法论——统计推断的逻辑"),
        (os.path.join(BOOK_DIR, "part2-理论篇", "ch06-因子合成与加权.md"), "第6章：因子合成与加权——最优性推导"),
    ]),
    ("第三篇 · 工具篇", [
        (os.path.join(BOOK_DIR, "part3-工具篇", "ch07-数据与工具基础.md"), "第7章：数据与工具基础——数据获取、清洗与Python工具链"),
        (os.path.join(BOOK_DIR, "part3-工具篇", "ch08-回测框架设计.md"), "第8章：回测框架设计——从零搭建一个简单回测引擎"),
    ]),
    ("第四篇 · 实践篇", [
        (os.path.join(BOOK_DIR, "part4-实践篇", "ch09-A股因子挖掘实战.md"), "第9章：A股因子挖掘实战——用真实数据构建因子库"),
        (os.path.join(BOOK_DIR, "part4-实践篇", "ch10-组合构建与优化.md"), "第10章：组合构建与优化——从因子得分到持仓权重"),
        (os.path.join(BOOK_DIR, "part4-实践篇", "ch11-完整策略开发.md"), "第11章：完整策略开发——端到端多因子策略实现"),
    ]),
    ("第五篇 · 进阶篇", [
        (os.path.join(BOOK_DIR, "part5-进阶篇", "ch12-风险管理与归因.md"), "第12章：风险管理与归因——理解你的收益从何而来"),
        (os.path.join(BOOK_DIR, "part5-进阶篇", "ch13-过拟合与陷阱.md"), "第13章：过拟合与陷阱——量化研究中的常见错误"),
        (os.path.join(BOOK_DIR, "part5-进阶篇", "ch14-从回测到实盘.md"), "第14章：从回测到实盘——现实世界的挑战"),
        (os.path.join(BOOK_DIR, "part5-进阶篇", "ch15-前沿方向与延伸阅读.md"), "第15章：前沿方向与延伸阅读——机器学习因子、另类数据"),
    ]),
    ("附录", [
        (os.path.join(BOOK_DIR, "appendix", "appendix-a-python快速入门.md"), "附录A：Python 快速入门"),
        (os.path.join(BOOK_DIR, "appendix", "appendix-b-数学回顾.md"), "附录B：线性代数与统计学回顾"),
        (os.path.join(BOOK_DIR, "appendix", "appendix-c-数据源与工具清单.md"), "附录C：推荐数据源与工具清单"),
        (os.path.join(BOOK_DIR, "appendix", "appendix-d-术语表.md"), "附录D：术语表（中英对照）"),
    ]),
]


def slugify(text):
    """将标题文本转换为可用于 HTML id 的 slug"""
    # 移除 markdown 格式标记
    text = re.sub(r'[#*`~]', '', text)
    # 中文保留，移除特殊字符
    text = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    return text


def extract_headings(md_text, max_level=3):
    """从 markdown 文本中提取标题，用于目录生成"""
    headings = []
    lines = md_text.split('\n')
    in_code_block = False
    for line in lines:
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        # 匹配 markdown 标题
        m = re.match(r'^(#{1,' + str(max_level) + r'})\s+(.+)', line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            # 跳过 "前置知识" 等引用块中的内容已在代码块外处理
            headings.append((level, title))
    return headings


def process_markdown_content(md_text, chapter_id):
    """
    处理 markdown 内容：
    1. 为标题添加 id 锚点
    2. 转换为 HTML
    """
    lines = md_text.split('\n')
    processed_lines = []
    in_code_block = False
    heading_counter = 0

    for line in lines:
        # 跟踪代码块状态
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            processed_lines.append(line)
            continue

        if not in_code_block:
            # 为 h2, h3 添加 id
            m = re.match(r'^(#{2,3})\s+(.+)', line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                heading_id = f"{chapter_id}-h{heading_counter}"
                heading_counter += 1
                processed_lines.append(f'{m.group(1)} <a id="{heading_id}"></a>{title}')
            else:
                processed_lines.append(line)
        else:
            processed_lines.append(line)

    md_text_processed = '\n'.join(processed_lines)

    # 转换 markdown -> HTML
    html = markdown.markdown(
        md_text_processed,
        extensions=['tables', 'fenced_code', 'toc', 'nl2br', 'sane_lists'],
        extension_configs={
            'toc': {'permalink': False}
        }
    )

    return html


def build_toc():
    """构建目录 HTML。

    注意：process_markdown_content 为正文中的每个 h2/h3 按出现顺序连续编号
    (h0, h1, h2 ...)。本函数必须使用相同的编号方式来生成锚点链接，
    否则目录链接会错位。具体做法：遍历所有 h2+h3，跳过第一个 h2（章节标题），
    对剩余的 h2 使用其全局索引作为 id。
    """
    toc_items = []
    chapter_num = 0

    for part_title, chapters in CHAPTERS:
        toc_items.append(f'<li class="toc-part">{escape(part_title)}</li>')
        for filepath, chapter_title in chapters:
            chapter_id = f"chapter-{chapter_num}"
            sub_items = []
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    md_text = f.read()
                # 提取所有 h2 和 h3（与 process_markdown_content 保持一致）
                all_headings = extract_headings(md_text, max_level=3)
                global_idx = 0          # 对应 process_markdown_content 中的 heading_counter
                first_h2_skipped = False

                for level, title in all_headings:
                    # 跳过 h1：build_content 会去掉每个文件的第一个 h1（章节大标题），
                    # process_markdown_content 只对 h2/h3 编号，所以这里也必须跳过 h1
                    # 且不递增 global_idx，否则锚点会整体偏移。
                    if level == 1:
                        continue

                    # 跳过第一个 h2（通常是章节正文的第一节，作为引言不显示在目录中）
                    if level == 2 and not first_h2_skipped:
                        first_h2_skipped = True
                        global_idx += 1
                        continue

                    # 只在目录中显示 h2（不显示 h3，避免目录过长）
                    if level == 2:
                        clean_title = re.sub(r'[#*`]', '', title).strip()
                        # 截断过长的标题
                        if len(clean_title) > 22:
                            clean_title = clean_title[:22] + "…"
                        sub_items.append(
                            f'<li class="toc-sub"><a href="#{chapter_id}-h{global_idx}">{escape(clean_title)}</a></li>'
                        )

                    global_idx += 1

            sub_html = ""
            if sub_items:
                sub_html = f'<ul class="toc-sublist">{"".join(sub_items)}</ul>'

            toc_items.append(
                f'<li class="toc-chapter"><a href="#{chapter_id}">{escape(chapter_title)}</a>{sub_html}</li>'
            )
            chapter_num += 1

    return f'<ul class="toc-list">{"".join(toc_items)}</ul>'


def build_content():
    """构建正文 HTML"""
    content_parts = []
    chapter_num = 0

    for part_title, chapters in CHAPTERS:
        content_parts.append(f'<div class="part-divider"><span>{escape(part_title)}</span></div>')

        for filepath, chapter_title in chapters:
            chapter_id = f"chapter-{chapter_num}"

            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    md_text = f.read()

                # 去掉第一个一级标题（# 开头），因为我们会用自定义标题
                lines = md_text.split('\n')
                start_idx = 0
                for i, line in enumerate(lines):
                    if re.match(r'^#\s+', line):
                        start_idx = i + 1
                        break
                md_text = '\n'.join(lines[start_idx:])

                # 检查是否为空内容（待撰写）
                content_stripped = md_text.strip()
                if not content_stripped or content_stripped == "> 待撰写":
                    chapter_html = '<p class="placeholder-text">本节内容待撰写，敬请期待。</p>'
                else:
                    chapter_html = process_markdown_content(md_text, chapter_id)
            else:
                chapter_html = '<p class="placeholder-text">文件未找到。</p>'

            content_parts.append(f'''
            <section class="chapter" id="{chapter_id}">
                <h1 class="chapter-title">{escape(chapter_title)}</h1>
                <div class="chapter-content">
                {chapter_html}
                </div>
            </section>
            ''')
            chapter_num += 1

    return '\n'.join(content_parts)


def generate_html():
    """生成完整的 HTML 文件"""
    toc_html = build_toc()
    content_html = build_content()

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多因子量化投资：从理论到实践</title>

    <!-- KaTeX for math rendering -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
        onload="renderMathInElement(document.body, {{
            delimiters: [
                {{left: '$$', right: '$$', display: true}},
                {{left: '$', right: '$', display: false}},
                {{left: '\\\\(', right: '\\\\)', display: false}},
                {{left: '\\\\[', right: '\\\\]', display: true}}
            ],
            throwOnError: false,
            ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
            ignoredClasses: ['highlight', 'codehilite']
        }});"></script>

    <!-- highlight.js for code blocks -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/atom-one-light.min.css">
    <script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/highlight.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/languages/python.min.js"></script>
    <script>hljs.highlightAll();</script>

    <style>
        /* ============================================================
           基础重置与变量
           ============================================================ */
        :root {{
            --bg-main: #faf9f6;
            --bg-sidebar: #f0ede5;
            --bg-content: #ffffff;
            --bg-code: #f5f3ee;
            --bg-code-inline: #efeae0;
            --bg-blockquote: #f8f6f0;
            --bg-table-head: #e8e4d8;
            --bg-table-alt: #f9f7f2;
            --bg-part-divider: #2c3e50;

            --color-text: #2b2b2b;
            --color-text-light: #5c5c5c;
            --color-heading: #1a1a2e;
            --color-accent: #1a5276;
            --color-accent-light: #2980b9;
            --color-link: #1a5276;
            --color-link-hover: #c0392b;
            --color-border: #d6d0c4;
            --color-code-text: #3d3d3d;
            --color-part-text: #ffffff;
            --color-toc-active: #1a5276;
            --color-blockquote-border: #c0a062;
            --color-blockquote-text: #5d5345;
            --color-warn-bg: #fdf6ec;
            --color-warn-border: #e6a23c;

            --font-serif: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "SimSun", serif;
            --font-sans: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
            --font-mono: "JetBrains Mono", "Fira Code", "Consolas", "Courier New", monospace;

            --sidebar-width: 300px;
            --content-max-width: 820px;
            --shadow-soft: 0 2px 8px rgba(0,0,0,0.06);
            --shadow-card: 0 4px 16px rgba(0,0,0,0.08);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html {{
            scroll-behavior: smooth;
            scroll-padding-top: 30px;
        }}

        body {{
            font-family: var(--font-sans);
            background: var(--bg-main);
            color: var(--color-text);
            line-height: 1.85;
            font-size: 16px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        /* ============================================================
           侧边栏目录
           ============================================================ */
        #sidebar {{
            position: fixed;
            top: 0;
            left: 0;
            width: var(--sidebar-width);
            height: 100vh;
            background: var(--bg-sidebar);
            border-right: 1px solid var(--color-border);
            overflow-y: auto;
            z-index: 100;
            transition: transform 0.3s ease;
        }}

        #sidebar::-webkit-scrollbar {{
            width: 6px;
        }}
        #sidebar::-webkit-scrollbar-track {{
            background: transparent;
        }}
        #sidebar::-webkit-scrollbar-thumb {{
            background: #c4bda8;
            border-radius: 3px;
        }}

        .sidebar-header {{
            padding: 30px 24px 20px;
            background: linear-gradient(135deg, #1a5276 0%, #2980b9 100%);
            color: #fff;
        }}

        .sidebar-header h1 {{
            font-size: 20px;
            font-weight: 700;
            line-height: 1.4;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
        }}

        .sidebar-header p {{
            font-size: 12px;
            opacity: 0.85;
            line-height: 1.5;
        }}

        .toc-container {{
            padding: 12px 0 40px;
        }}

        .toc-list {{
            list-style: none;
        }}

        .toc-part {{
            padding: 14px 24px 6px;
            font-size: 12px;
            font-weight: 700;
            color: var(--color-text-light);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 6px;
        }}

        .toc-chapter {{
            position: relative;
        }}

        .toc-chapter > a {{
            display: block;
            padding: 7px 24px 7px 28px;
            font-size: 13.5px;
            color: var(--color-text);
            text-decoration: none;
            transition: all 0.15s ease;
            border-left: 3px solid transparent;
            line-height: 1.5;
        }}

        .toc-chapter > a:hover {{
            background: rgba(26, 82, 118, 0.06);
            color: var(--color-accent);
        }}

        .toc-chapter.active > a {{
            background: rgba(26, 82, 118, 0.1);
            border-left-color: var(--color-accent);
            color: var(--color-accent);
            font-weight: 600;
        }}

        .toc-sublist {{
            list-style: none;
            padding-left: 0;
            margin-bottom: 2px;
        }}

        .toc-sub {{
            /* */
        }}

        .toc-sub a {{
            display: block;
            padding: 3px 24px 3px 44px;
            font-size: 12px;
            color: var(--color-text-light);
            text-decoration: none;
            transition: color 0.15s;
            line-height: 1.5;
        }}

        .toc-sub a:hover {{
            color: var(--color-accent);
        }}

        /* ============================================================
           主内容区
           ============================================================ */
        #main {{
            margin-left: var(--sidebar-width);
            padding: 0 0 80px;
            min-height: 100vh;
        }}

        .content-wrapper {{
            max-width: var(--content-max-width);
            margin: 0 auto;
            padding: 50px 50px;
        }}

        /* 阅读进度条 */
        #progress-bar {{
            position: fixed;
            top: 0;
            left: var(--sidebar-width);
            right: 0;
            height: 3px;
            background: var(--color-accent);
            z-index: 200;
            width: 0%;
            transition: width 0.1s;
        }}

        /* 移动端菜单按钮 */
        #menu-toggle {{
            display: none;
            position: fixed;
            top: 16px;
            left: 16px;
            z-index: 150;
            background: var(--color-accent);
            color: #fff;
            border: none;
            border-radius: 6px;
            padding: 8px 14px;
            font-size: 14px;
            cursor: pointer;
            box-shadow: var(--shadow-card);
        }}

        /* ============================================================
           章节样式
           ============================================================ */
        .part-divider {{
            text-align: center;
            margin: 60px 0 40px;
            position: relative;
        }}

        .part-divider span {{
            display: inline-block;
            background: var(--bg-part-divider);
            color: var(--color-part-text);
            padding: 8px 28px;
            font-size: 15px;
            font-weight: 600;
            letter-spacing: 2px;
            border-radius: 3px;
        }}

        .chapter {{
            margin-bottom: 50px;
            scroll-margin-top: 30px;
        }}

        .chapter-title {{
            font-family: var(--font-serif);
            font-size: 28px;
            font-weight: 800;
            color: var(--color-heading);
            line-height: 1.4;
            padding-bottom: 16px;
            margin-bottom: 30px;
            border-bottom: 3px solid var(--color-accent);
            position: relative;
        }}

        .chapter-title::after {{
            content: '';
            position: absolute;
            bottom: -3px;
            left: 0;
            width: 60px;
            height: 3px;
            background: var(--color-link-hover);
        }}

        .chapter-content h2 {{
            font-family: var(--font-serif);
            font-size: 22px;
            font-weight: 700;
            color: var(--color-heading);
            margin-top: 48px;
            margin-bottom: 18px;
            padding-left: 14px;
            border-left: 4px solid var(--color-accent);
            line-height: 1.5;
        }}

        .chapter-content h3 {{
            font-size: 18px;
            font-weight: 700;
            color: var(--color-heading);
            margin-top: 36px;
            margin-bottom: 14px;
            line-height: 1.5;
        }}

        .chapter-content h4 {{
            font-size: 16px;
            font-weight: 700;
            color: var(--color-accent);
            margin-top: 24px;
            margin-bottom: 10px;
        }}

        .chapter-content p {{
            margin-bottom: 18px;
            text-align: justify;
            color: var(--color-text);
            line-height: 1.95;
        }}

        /* 引用块 */
        .chapter-content blockquote {{
            background: var(--bg-blockquote);
            border-left: 4px solid var(--color-blockquote-border);
            margin: 20px 0;
            padding: 16px 22px;
            border-radius: 0 6px 6px 0;
            color: var(--color-blockquote-text);
        }}

        .chapter-content blockquote p {{
            margin-bottom: 8px;
            color: var(--color-blockquote-text);
        }}

        .chapter-content blockquote p:last-child {{
            margin-bottom: 0;
        }}

        /* 表格 */
        .chapter-content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 22px 0;
            font-size: 14px;
            box-shadow: var(--shadow-soft);
            border-radius: 6px;
            overflow: hidden;
        }}

        .chapter-content thead {{
            background: var(--bg-table-head);
        }}

        .chapter-content th {{
            padding: 12px 14px;
            text-align: left;
            font-weight: 700;
            color: var(--color-heading);
            border-bottom: 2px solid var(--color-border);
            white-space: nowrap;
        }}

        .chapter-content td {{
            padding: 10px 14px;
            border-bottom: 1px solid var(--color-border);
            color: var(--color-text);
        }}

        .chapter-content tbody tr:nth-child(even) {{
            background: var(--bg-table-alt);
        }}

        .chapter-content tbody tr:hover {{
            background: #eef2f7;
        }}

        /* 列表 */
        .chapter-content ul,
        .chapter-content ol {{
            margin: 12px 0 18px 0;
            padding-left: 26px;
        }}

        .chapter-content li {{
            margin-bottom: 6px;
            line-height: 1.85;
        }}

        /* 行内代码 */
        .chapter-content code {{
            font-family: var(--font-mono);
            font-size: 0.88em;
            background: var(--bg-code-inline);
            color: var(--color-code-text);
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid rgba(0,0,0,0.06);
        }}

        /* 代码块 */
        .chapter-content pre {{
            background: var(--bg-code);
            border: 1px solid var(--color-border);
            border-radius: 8px;
            padding: 18px 20px;
            overflow-x: auto;
            margin: 20px 0;
            font-size: 13.5px;
            line-height: 1.65;
            box-shadow: var(--shadow-soft);
        }}

        .chapter-content pre code {{
            background: none;
            border: none;
            padding: 0;
            font-size: inherit;
            color: var(--color-code-text);
        }}

        /* 数学公式 */
        .katex {{
            font-size: 1.05em;
        }}

        .katex-display {{
            margin: 20px 0;
            padding: 14px 0;
            overflow-x: auto;
            overflow-y: hidden;
        }}

        /* 水平线 */
        .chapter-content hr {{
            border: none;
            border-top: 1px solid var(--color-border);
            margin: 36px 0;
            position: relative;
        }}

        .chapter-content hr::after {{
            content: '❖';
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--bg-content);
            padding: 0 12px;
            color: var(--color-blockquote-border);
            font-size: 14px;
        }}

        /* 链接 */
        .chapter-content a {{
            color: var(--color-link);
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: all 0.15s;
        }}

        .chapter-content a:hover {{
            color: var(--color-link-hover);
            border-bottom-color: var(--color-link-hover);
        }}

        /* 占位文字 */
        .placeholder-text {{
            text-align: center;
            color: var(--color-text-light);
            font-style: italic;
            padding: 40px;
            background: var(--bg-blockquote);
            border-radius: 8px;
        }}

        /* 强调 */
        .chapter-content strong {{
            font-weight: 700;
            color: var(--color-heading);
        }}

        /* ============================================================
           返回顶部按钮
           ============================================================ */
        #back-to-top {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 44px;
            height: 44px;
            background: var(--color-accent);
            color: #fff;
            border: none;
            border-radius: 50%;
            font-size: 20px;
            cursor: pointer;
            box-shadow: var(--shadow-card);
            z-index: 90;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        #back-to-top.visible {{
            opacity: 1;
            visibility: visible;
        }}

        #back-to-top:hover {{
            background: var(--color-accent-light);
            transform: translateY(-2px);
        }}

        /* ============================================================
           响应式
           ============================================================ */
        @media (max-width: 1024px) {{
            :root {{
                --sidebar-width: 260px;
            }}
            .content-wrapper {{
                padding: 40px 30px;
            }}
        }}

        @media (max-width: 768px) {{
            #menu-toggle {{
                display: block;
            }}

            #sidebar {{
                transform: translateX(-100%);
            }}

            #sidebar.open {{
                transform: translateX(0);
            }}

            #main {{
                margin-left: 0;
            }}

            #progress-bar {{
                left: 0;
            }}

            .content-wrapper {{
                padding: 30px 20px 60px;
            }}

            .chapter-title {{
                font-size: 22px;
            }}

            .chapter-content h2 {{
                font-size: 19px;
            }}

            .chapter-content h3 {{
                font-size: 16px;
            }}

            .chapter-content table {{
                font-size: 12px;
            }}

            .chapter-content th,
            .chapter-content td {{
                padding: 8px 10px;
            }}

            .chapter-content pre {{
                font-size: 12px;
                padding: 14px;
            }}
        }}

        /* 打印优化 */
        @media print {{
            #sidebar, #back-to-top, #menu-toggle, #progress-bar {{
                display: none;
            }}
            #main {{
                margin-left: 0;
            }}
            .content-wrapper {{
                max-width: 100%;
                padding: 0;
            }}
            .chapter {{
                page-break-after: always;
            }}
        }}
    </style>
</head>
<body>

    <!-- 阅读进度条 -->
    <div id="progress-bar"></div>

    <!-- 移动端菜单按钮 -->
    <button id="menu-toggle">☰ 目录</button>

    <!-- 侧边栏目录 -->
    <nav id="sidebar">
        <div class="sidebar-header">
            <h1>多因子量化投资</h1>
            <p>从理论到实践 · A股散户的量化之路</p>
        </div>
        <div class="toc-container">
            {toc_html}
        </div>
    </nav>

    <!-- 主内容 -->
    <div id="main">
        <div class="content-wrapper">
            {content_html}
        </div>
    </div>

    <!-- 返回顶部 -->
    <button id="back-to-top" title="返回顶部">↑</button>

    <script>
        // ============================================================
        // 移动端菜单切换
        // ============================================================
        const menuToggle = document.getElementById('menu-toggle');
        const sidebar = document.getElementById('sidebar');
        menuToggle.addEventListener('click', () => {{
            sidebar.classList.toggle('open');
        }});

        // 点击目录链接后关闭侧边栏（移动端）
        document.querySelectorAll('#sidebar a').forEach(link => {{
            link.addEventListener('click', () => {{
                if (window.innerWidth <= 768) {{
                    sidebar.classList.remove('open');
                }}
            }});
        }});

        // ============================================================
        // 阅读进度条
        // ============================================================
        const progressBar = document.getElementById('progress-bar');
        window.addEventListener('scroll', () => {{
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            const progress = (scrollTop / scrollHeight) * 100;
            progressBar.style.width = progress + '%';
        }});

        // ============================================================
        // 返回顶部
        // ============================================================
        const backToTop = document.getElementById('back-to-top');
        window.addEventListener('scroll', () => {{
            if (window.pageYOffset > 400) {{
                backToTop.classList.add('visible');
            }} else {{
                backToTop.classList.remove('visible');
            }}
        }});
        backToTop.addEventListener('click', () => {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});

        // ============================================================
        // 目录高亮当前章节
        // ============================================================
        const chapters = document.querySelectorAll('.chapter');
        const tocLinks = document.querySelectorAll('.toc-chapter > a');

        function highlightCurrentChapter() {{
            let current = '';
            const scrollPos = window.pageYOffset + 100;

            chapters.forEach(chapter => {{
                const top = chapter.offsetTop;
                const height = chapter.offsetHeight;
                if (scrollPos >= top && scrollPos < top + height) {{
                    current = chapter.id;
                }}
            }});

            tocLinks.forEach(link => {{
                const href = link.getAttribute('href');
                if (href === '#' + current) {{
                    link.parentElement.classList.add('active');
                }} else {{
                    link.parentElement.classList.remove('active');
                }}
            }});
        }}

        window.addEventListener('scroll', highlightCurrentChapter);
        highlightCurrentChapter();
    </script>
</body>
</html>'''

    return html


if __name__ == '__main__':
    html_content = generate_html()
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML 文件已生成: {OUTPUT_FILE}")
    file_size = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"文件大小: {file_size:.1f} KB")
