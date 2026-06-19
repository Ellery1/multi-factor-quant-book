#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将多因子量化投资书籍的所有 Markdown 章节整合为一个排版精美的 HTML 电子书。

特性：
- MathJax 3.x 渲染数学公式（行内 $...$ 和块级 $$...$$）
- 楷体正文 + 黑体标题，暖色调纸质书配色
- 左侧固定侧边栏目录，IntersectionObserver 自动高亮当前章节
- 响应式设计：PC / 平板 / 手机（抽屉式菜单）
- 章节卡片布局，首行缩进，斑马纹表格，深色代码块
- 页头渐变背景 + 金色标题，页脚版权信息
- 回到顶部按钮，打印样式，暗色模式
"""

import os
import re
import markdown
from html import escape
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BOOK_DIR = os.path.join(PROJECT_DIR, "book")
OUTPUT_FILE = os.path.join(PROJECT_DIR, "multi-factor-quant-book.html")
BOOK_TITLE = "多因子量化投资：从理论到实践"

# ============================================================
# 章节定义：按书籍顺序
# ============================================================
CHAPTERS = [
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
    ("第三篇 · 工具篇", [
        (os.path.join(BOOK_DIR, "part3-工具篇", "ch07-数据与工具基础.md"),),
        (os.path.join(BOOK_DIR, "part3-工具篇", "ch08-回测框架设计.md"),),
    ]),
    ("第四篇 · 实践篇", [
        (os.path.join(BOOK_DIR, "part4-实践篇", "ch09-A股因子挖掘实战.md"),),
        (os.path.join(BOOK_DIR, "part4-实践篇", "ch10-组合构建与优化.md"),),
        (os.path.join(BOOK_DIR, "part4-实践篇", "ch11-完整策略开发.md"),),
    ]),
    ("第五篇 · 进阶篇", [
        (os.path.join(BOOK_DIR, "part5-进阶篇", "ch12-风险管理与归因.md"),),
        (os.path.join(BOOK_DIR, "part5-进阶篇", "ch13-过拟合与陷阱.md"),),
        (os.path.join(BOOK_DIR, "part5-进阶篇", "ch14-从回测到实盘.md"),),
        (os.path.join(BOOK_DIR, "part5-进阶篇", "ch15-前沿方向与延伸阅读.md"),),
    ]),
    ("附录", [
        (os.path.join(BOOK_DIR, "appendix", "appendix-a-python快速入门.md"),),
        (os.path.join(BOOK_DIR, "appendix", "appendix-b-数学回顾.md"),),
        (os.path.join(BOOK_DIR, "appendix", "appendix-c-数据源与工具清单.md"),),
        (os.path.join(BOOK_DIR, "appendix", "appendix-d-术语表.md"),),
    ]),
]


# ============================================================
# 数学公式保护：防止 markdown 库破坏 LaTeX 语法
# ============================================================

def protect_math(md_text):
    """提取 $$...$$ 和 $...$ 公式，替换为占位符，防止 markdown 破坏 LaTeX 语法。"""
    placeholders = {}

    def save_math(match, prefix):
        key = f"{prefix}MATHPLACEHOLDER{len(placeholders)}ENDMATH"
        placeholders[key] = match.group(0)
        return key

    # 1. 先保护代码块内的内容（避免把代码里的 $ 误识别为公式）
    code_blocks = {}
    def save_code(match):
        key = f"CODEBLOCKPLACEHOLDER{len(code_blocks)}ENDCODE"
        code_blocks[key] = match.group(0)
        return key

    md_text = re.sub(r'```[\s\S]*?```', save_code, md_text)
    md_text = re.sub(r'`[^`]+`', save_code, md_text)

    # 2. 保护 $$...$$ (块级公式，可跨行)
    md_text = re.sub(r'\$\$[\s\S]*?\$\$', lambda m: save_math(m, 'DISPLAY'), md_text)

    # 3. 保护 $...$ (行内公式，不跨行，排除 $$)
    md_text = re.sub(r'(?<!\$)\$(?!\$)([^\$\n]+?)\$(?!\$)', lambda m: save_math(m, 'INLINE'), md_text)

    # 4. 恢复代码块
    for key, val in code_blocks.items():
        md_text = md_text.replace(key, val)

    return md_text, placeholders


def restore_math(html_text, placeholders):
    """在 markdown 转 HTML 后，将占位符替换回原始公式。"""
    for key, val in placeholders.items():
        html_text = html_text.replace(key, val)
    return html_text


# ============================================================
# 标题提取与处理
# ============================================================

def extract_headings(md_text):
    """提取 h1 和 h2 标题（跳过代码块内的 # 开头行）。
    返回 [(level, title), ...]
    """
    headings = []
    lines = md_text.split('\n')
    in_code_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        m = re.match(r'^(#{1,3})\s+(.+)', line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            headings.append((level, title))
    return headings


def fix_markdown_lists(md_text):
    lines = md_text.split('\n')
    new_lines = []
    in_code_block = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue
        if in_code_block:
            new_lines.append(line)
            continue

        list_match = re.match(r'^(\s*)(- |\d+\.\s)', line)
        is_list_line = list_match is not None

        # Fix 1: add blank line before list following non-list line
        if is_list_line and i > 0:
            prev = lines[i - 1]
            prev_s = prev.strip()
            prev_is_list = bool(re.match(r'^(\s*)(- |\d+\.\s)', prev))
            if (prev_s and not prev_is_list
                    and not prev_s.startswith('>')
                    and not prev_s.startswith('#')
                    and not prev_s.startswith('|')
                    and not prev_s.startswith('$$')):
                new_lines.append('')

        # Fix 2: ensure sub-list has >= 4 spaces indent
        if list_match and i > 0:
            indent = len(list_match.group(1))
            if 0 < indent < 4:
                prev_match = re.match(r'^(\s*)(- |\d+\.\s)', lines[i - 1])
                if prev_match:
                    missing = 4 - indent
                    line = ' ' * missing + line

        new_lines.append(line)

    return '\n'.join(new_lines)


def process_markdown(md_text, chapter_idx, heading_ids):
    """将 markdown 转换为 HTML，并为 h1/h2 添加锚点 id。
    heading_ids: dict，记录每个标题的锚点 id（由 build_toc 和本函数共用）
    """
    # 保护数学公式
    md_text, math_placeholders = protect_math(md_text)

    lines = md_text.split('\n')
    processed_lines = []
    in_code_block = False
    h_counter = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            processed_lines.append(line)
            continue

        if not in_code_block:
            # 为 h1/h2/h3 添加锚点
            m = re.match(r'^(#{1,3})\s+(.+)', line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                anchor_id = f"ch{chapter_idx}-h{h_counter}"
                heading_ids[(chapter_idx, h_counter)] = (level, title, anchor_id)
                h_counter += 1
                # 用 HTML 标签替代 markdown 标题，以便嵌入锚点
                tag = f'h{level}'
                processed_lines.append(f'<{tag} id="{anchor_id}">{escape(title)}</{tag}>')
                continue

        processed_lines.append(line)

    md_text_processed = '\n'.join(processed_lines)

    # 转换 markdown -> HTML（不使用 nl2br，避免多余 <br> 标签）
    html = markdown.markdown(
        md_text_processed,
        extensions=['tables', 'fenced_code', 'sane_lists'],
    )

    # 恢复数学公式
    html = restore_math(html, math_placeholders)

    return html


def fix_image_paths(html, md_filepath):
    """将 markdown 中的相对图片路径改写为相对 HTML 输出文件的路径。

    md_filepath 是相对于项目根目录的路径（如 book/part2-理论篇/ch03-因子的本质.md）。
    HTML 输出在项目根目录，所以图片路径需要从 markdown 所在目录映射到根目录。
    """
    md_dir = os.path.dirname(md_filepath)  # e.g. book/part2-理论篇

    def rewrite_src(match):
        src = match.group(1)
        # 跳过外部 URL
        if src.startswith(('http://', 'https://', 'data:')):
            return match.group(0)
        # 解析相对路径
        abs_src = os.path.normpath(os.path.join(md_dir, src)).replace('\\', '/')
        return f'src="{abs_src}"'

    html = re.sub(r'src="([^"]+)"', rewrite_src, html)
    return html


# ============================================================
# 目录构建
# ============================================================

def build_toc(all_heading_ids):
    """构建侧边栏目录 HTML。
    all_heading_ids: list of (chapter_idx, heading_ids_dict)
    返回 (toc_html, all_anchors) 其中 all_anchors 用于 IntersectionObserver
    """
    toc_items = []
    all_anchors = []

    for part_title, chapters_in_part, part_heading_ids in all_heading_ids:
        toc_items.append(f'<li class="toc-part">{escape(part_title)}</li>')

        for chapter_idx, heading_ids in chapters_in_part:
            chapter_headings = [(k, v) for k, v in heading_ids.items()]
            chapter_headings.sort(key=lambda x: x[0])

            if not chapter_headings:
                continue

            # 第一个 h1 是章节标题
            h1_entry = None
            h2_entries = []
            h3_by_h2 = {}
            for (idx, (level, title, anchor_id)) in chapter_headings:
                if level == 1:
                    h1_entry = (title, anchor_id)
                elif level == 2:
                    h2_entries.append((title, anchor_id))
                    h3_by_h2[(title, anchor_id)] = []
                elif level == 3:
                    if h2_entries:
                        h3_by_h2[h2_entries[-1]].append((title, anchor_id))
                all_anchors.append(anchor_id)

            if h1_entry:
                title, anchor_id = h1_entry
                toc_items.append(
                    f'<li class="toc-chapter" data-anchor="{anchor_id}">'
                    f'<a href="#{anchor_id}">{escape(title)}</a>'
                )

                if h2_entries:
                    sub_items = []
                    for sub_title, sub_id in h2_entries:
                        display = sub_title if len(sub_title) <= 24 else sub_title[:24] + '…'
                        sub_items.append(
                            f'<li class="toc-section" data-anchor="{sub_id}">'
                            f'<a href="#{sub_id}">{escape(display)}</a></li>'
                        )
                        # 如果有 h3 子标题
                        h3_list = h3_by_h2.get((sub_title, sub_id), [])
                        if h3_list:
                            sub_sub = []
                            for h3_title, h3_id in h3_list:
                                h3_display = h3_title if len(h3_title) <= 28 else h3_title[:28] + '…'
                                sub_sub.append(
                                    f'<li class="toc-subsection" data-anchor="{h3_id}">'
                                    f'<a href="#{h3_id}">{escape(h3_display)}</a></li>'
                                )
                            sub_items.append(f'<ul class="toc-subsections">{"".join(sub_sub)}</ul>')
                    toc_items.append(f'<ul class="toc-sections">{"".join(sub_items)}</ul>')

                toc_items.append('</li>')

    return '\n'.join(toc_items), all_anchors


# ============================================================
# 正文构建
# ============================================================

def build_content(all_heading_ids):
    """构建正文 HTML。"""
    content_parts = []

    for part_title, chapters_in_part, part_heading_ids in all_heading_ids:
        content_parts.append(f'<div class="part-divider"><span>{escape(part_title)}</span></div>')

        for chapter_idx, heading_ids in chapters_in_part:
            filepath = chapters_in_part[0] if isinstance(chapters_in_part, tuple) else None
            # 找到文件路径
            # chapters_in_part 结构已变，需要从 all_heading_ids 调用时传入
            pass

    return '\n'.join(content_parts)


def build_content_v2(chapter_data):
    """构建正文 HTML。
    chapter_data: list of (part_title, [(filepath, chapter_idx, heading_ids), ...], ...)
    """
    content_parts = []

    for part_title, chapters in chapter_data:
        content_parts.append(f'<div class="part-divider"><span>{escape(part_title)}</span></div>')

        for filepath, chapter_idx, heading_ids in chapters:
            if not os.path.exists(filepath):
                content_parts.append(f'''
                <section class="chapter-card" id="ch{chapter_idx}-card">
                    <p class="placeholder">文件未找到：{escape(filepath)}</p>
                </section>''')
                continue

            with open(filepath, 'r', encoding='utf-8') as f:
                md_text = f.read()

            # 预处理：修复列表格式，确保 markdown 转换器能正确渲染
            md_text = fix_markdown_lists(md_text)

            content_stripped = md_text.strip()
            if not content_stripped or content_stripped == "> 待撰写":
                # 提取 h1 标题
                headings = extract_headings(md_text)
                h1_title = headings[0][1] if headings and headings[0][0] == 1 else "待撰写"
                content_parts.append(f'''
                <section class="chapter-card" id="ch{chapter_idx}-card">
                    <h1 id="ch{chapter_idx}-h0">{escape(h1_title)}</h1>
                    <p class="placeholder">本节内容待撰写，敬请期待。</p>
                </section>''')
                heading_ids[(chapter_idx, 0)] = (1, h1_title, f"ch{chapter_idx}-h0")
                continue

            html = process_markdown(md_text, chapter_idx, heading_ids)
            html = fix_image_paths(html, os.path.relpath(filepath, PROJECT_DIR))
            content_parts.append(f'''
            <section class="chapter-card" id="ch{chapter_idx}-card">
                {html}
            </section>''')

    return '\n'.join(content_parts)


# ============================================================
# HTML 模板
# ============================================================

def generate_html():
    """生成完整的 HTML 文件。"""

    # 第一遍：读取所有文件，收集标题信息
    chapter_data = []
    all_heading_ids_for_toc = []
    chapter_counter = 0

    for part_title, chapters_in_part in CHAPTERS:
        chapters_info = []
        part_heading_ids = []

        for chapter_tuple in chapters_in_part:
            filepath = chapter_tuple[0]
            chapter_idx = chapter_counter
            heading_ids = {}

            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    md_text = f.read()
                headings = extract_headings(md_text)
                for i, (level, title) in enumerate(headings):
                    anchor_id = f"ch{chapter_idx}-h{i}"
                    heading_ids[(chapter_idx, i)] = (level, title, anchor_id)

            chapters_info.append((filepath, chapter_idx, heading_ids))
            part_heading_ids.append((chapter_idx, heading_ids))
            chapter_counter += 1

        chapter_data.append((part_title, chapters_info))
        all_heading_ids_for_toc.append((part_title, part_heading_ids, None))

    # 构建目录
    toc_html, all_anchors = build_toc(all_heading_ids_for_toc)

    # 构建正文
    content_html = build_content_v2(chapter_data)

    # 生成日期
    gen_date = datetime.now().strftime('%Y年%m月%d日')

    # 文件列表
    file_list = []
    for part_title, chapters_in_part in CHAPTERS:
        for chapter_tuple in chapters_in_part:
            filepath = chapter_tuple[0]
            filename = os.path.basename(filepath)
            file_list.append(filename)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(BOOK_TITLE)}</title>

    <!-- MathJax 3.x -->
    <script>
        window.MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
                processEscapes: true,
                tags: 'ams'
            }},
            chtml: {{
                scale: 1.0,
                matchFontHeight: false
            }},
            startup: {{
                ready: () => {{
                    MathJax.startup.defaultReady();
                }}
            }}
        }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>

    <style>
        /* ============================================================
           CSS 自定义属性
           ============================================================ */
        :root {{
            /* 配色 */
            --bg-page: #faf8f5;
            --bg-card: #fffef9;
            --bg-sidebar: #f3efe8;
            --bg-code: #1e1e2e;
            --bg-code-inline: #efeae0;
            --bg-blockquote: #fdf9ed;
            --bg-table-head: #e8e2d3;
            --bg-table-alt: #f9f6f0;
            --bg-header-start: #0f1c3f;
            --bg-header-end: #1a3158;
            --bg-toc-active: rgba(26, 82, 118, 0.08);

            --color-text: #333333;
            --color-heading: #1a1a2e;
            --color-secondary: #777777;
            --color-accent: #1a5276;
            --color-accent-light: #2980b9;
            --color-gold: #c0a062;
            --color-link: #1a5276;
            --color-link-hover: #c0392b;
            --color-border: #d8d2c5;
            --color-blockquote-border: #c0a062;
            --color-code-text: #e0e0e0;
            --color-placeholder: #999999;

            /* 字体 */
            --font-body: "KaiTi", "STKaiti", "楷体", "Noto Serif SC", "Songti SC", serif;
            --font-heading: "SimHei", "STHeiti", "黑体", "PingFang SC", "Microsoft YaHei", sans-serif;
            --font-code: "Fira Code", "JetBrains Mono", "Consolas", "Courier New", monospace;

            /* 尺寸 */
            --sidebar-width: 260px;
            --content-max-width: 800px;
            --font-size-body: 17px;
            --line-height-body: 1.95;
            --letter-spacing-body: 0.03em;
            --card-radius: 12px;
            --card-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
            --transition: 0.3s ease;
        }}

        /* 暗色模式 */
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-page: #1a1a2e;
                --bg-card: #232340;
                --bg-sidebar: #1e1e36;
                --bg-code: #0d0d1a;
                --bg-code-inline: #2a2a48;
                --bg-blockquote: #2a2840;
                --bg-table-head: #2a2a48;
                --bg-table-alt: #1f1f38;

                --color-text: #c8c8d8;
                --color-heading: #e0e0f0;
                --color-secondary: #8888a8;
                --color-border: #3a3a58;
                --color-blockquote-border: #8a7a4a;
            }}
        }}

        /* ============================================================
           基础重置
           ============================================================ */
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
            font-family: var(--font-body);
            background: var(--bg-page);
            color: var(--color-text);
            font-size: var(--font-size-body);
            line-height: var(--line-height-body);
            letter-spacing: var(--letter-spacing-body);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        /* ============================================================
           页头
           ============================================================ */
        .page-header {{
            background: linear-gradient(135deg, var(--bg-header-start) 0%, var(--bg-header-end) 100%);
            padding: 60px 20px 50px;
            text-align: center;
            margin-bottom: 0;
        }}

        .page-header h1 {{
            font-family: var(--font-heading);
            font-size: 2.2em;
            font-weight: 800;
            background: linear-gradient(135deg, #d4af37 0%, #f0d080 50%, #d4af37 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: 0.08em;
            margin-bottom: 12px;
        }}

        .page-header .subtitle {{
            color: rgba(255, 255, 255, 0.65);
            font-size: 0.95em;
            letter-spacing: 0.1em;
        }}

        /* ============================================================
           布局
           ============================================================ */
        .layout {{
            display: flex;
            align-items: flex-start;
        }}

        /* ============================================================
           侧边栏目录
           ============================================================ */
        #sidebar {{
            position: sticky;
            top: 0;
            width: var(--sidebar-width);
            height: 100vh;
            background: var(--bg-sidebar);
            border-right: 1px solid var(--color-border);
            overflow-y: auto;
            flex-shrink: 0;
            z-index: 100;
            transition: transform var(--transition);
        }}

        #sidebar::-webkit-scrollbar {{
            width: 5px;
        }}
        #sidebar::-webkit-scrollbar-track {{
            background: transparent;
        }}
        #sidebar::-webkit-scrollbar-thumb {{
            background: #c0b8a0;
            border-radius: 3px;
        }}

        .sidebar-header {{
            padding: 24px 20px 16px;
            border-bottom: 1px solid var(--color-border);
        }}

        .sidebar-header h2 {{
            font-family: var(--font-heading);
            font-size: 15px;
            color: var(--color-heading);
            letter-spacing: 0.05em;
        }}

        .toc-nav {{
            padding: 8px 0 40px;
        }}

        .toc-nav ul {{
            list-style: none;
        }}

        .toc-part {{
            padding: 14px 20px 6px;
            font-size: 11px;
            font-weight: 700;
            font-family: var(--font-heading);
            color: var(--color-secondary);
            letter-spacing: 1.5px;
        }}

        .toc-chapter {{
            position: relative;
        }}

        .toc-chapter > a {{
            display: block;
            padding: 6px 20px 6px 24px;
            font-size: 13.5px;
            color: var(--color-text);
            text-decoration: none;
            transition: all 0.15s ease;
            border-left: 3px solid transparent;
            line-height: 1.5;
            font-family: var(--font-heading);
        }}

        .toc-chapter > a:hover {{
            background: var(--bg-toc-active);
            color: var(--color-accent);
        }}

        .toc-chapter.active > a {{
            background: var(--bg-toc-active);
            border-left-color: var(--color-accent);
            color: var(--color-accent);
            font-weight: 600;
        }}

        .toc-sections {{
            padding-bottom: 3px;
        }}

        .toc-section a {{
            display: block;
            padding: 3px 20px 3px 40px;
            font-size: 12px;
            color: var(--color-text);
            text-decoration: none;
            transition: color 0.15s;
            line-height: 1.5;
            font-family: var(--font-body);
        }}

        .toc-section a:hover {{
            color: var(--color-accent);
        }}

        .toc-section.active a {{
            color: var(--color-accent);
            font-weight: 600;
        }}

        .toc-subsections {{
            padding-bottom: 2px;
        }}

        .toc-subsection a {{
            display: block;
            padding: 2px 20px 2px 56px;
            font-size: 11px;
            color: #999;
            text-decoration: none;
            transition: color 0.15s;
            line-height: 1.5;
            font-family: var(--font-body);
        }}

        .toc-subsection a:hover {{
            color: var(--color-accent);
        }}

        .toc-subsection.active a {{
            color: var(--color-accent);
            font-weight: 600;
        }}

        /* ============================================================
           主内容区
           ============================================================ */
        #main {{
            flex: 1;
            padding: 30px 0 80px;
            min-width: 0; /* 防止 flex 子元素溢出 */
        }}

        .content-wrapper {{
            width: var(--content-max-width);
            min-width: 360px;
            max-width: 95vw;
            margin: 0 auto;
            padding: 0 40px;
            position: relative;
            border-left: 2px dashed var(--color-border);
            border-right: 2px dashed var(--color-border);
            border-bottom: 2px dashed var(--color-border);
            border-bottom-left-radius: 8px;
            border-bottom-right-radius: 8px;
        }}

        /* 右边缘拖拽把手 —— 鼠标靠近右边界自动变成可拖拽状态 */
        .drag-handle {{
            position: absolute;
            top: 0;
            right: -12px;
            width: 24px;
            height: 100%;
            cursor: ew-resize;
            z-index: 10;
            background: transparent;
        }}

        .drag-handle::after {{
            content: "";
            position: absolute;
            right: 6px;
            top: 50%;
            transform: translateY(-50%);
            width: 3px;
            height: 60px;
            border-radius: 2px;
            background: var(--color-secondary);
            opacity: 0.2;
            transition: opacity 0.2s;
        }}

        .content-wrapper:hover .drag-handle::after,
        .drag-handle:active::after {{
            opacity: 0.6;
        }}

        /* 篇分割线 */
        .part-divider {{
            text-align: center;
            margin: 50px 0 30px;
        }}

        .part-divider span {{
            display: inline-block;
            background: var(--color-heading);
            color: #fff;
            padding: 6px 24px;
            font-size: 14px;
            font-family: var(--font-heading);
            font-weight: 600;
            letter-spacing: 2px;
            border-radius: 3px;
        }}

        /* 章节卡片 */
        .chapter-card {{
            background: var(--bg-card);
            border-radius: var(--card-radius);
            box-shadow: var(--card-shadow);
            padding: 36px 40px;
            margin-bottom: 30px;
            scroll-margin-top: 20px;
        }}

        /* 标题 */
        .chapter-card h1 {{
            font-family: var(--font-heading);
            font-size: 1.7em;
            font-weight: 800;
            color: var(--color-heading);
            line-height: 1.4;
            padding-bottom: 14px;
            margin-bottom: 24px;
            border-bottom: 2px solid var(--color-gold);
            letter-spacing: 0.02em;
        }}

        .chapter-card h2 {{
            font-family: var(--font-heading);
            font-size: 1.3em;
            font-weight: 700;
            color: var(--color-heading);
            margin-top: 40px;
            margin-bottom: 14px;
            padding-left: 12px;
            border-left: 4px solid var(--color-accent);
            line-height: 1.5;
        }}

        .chapter-card h3 {{
            font-family: var(--font-heading);
            font-size: 1.1em;
            font-weight: 700;
            color: var(--color-accent);
            margin-top: 28px;
            margin-bottom: 10px;
        }}

        .chapter-card h4 {{
            font-family: var(--font-heading);
            font-size: 1em;
            font-weight: 700;
            color: var(--color-heading);
            margin-top: 20px;
            margin-bottom: 8px;
        }}

        /* 段落 + 首行缩进 */
        .chapter-card p {{
            margin-bottom: 1.1em;
            text-align: justify;
            line-height: var(--line-height-body);
            text-indent: 2em;
        }}

        /* 引用块、列表、代码块中的段落不缩进 */
        .chapter-card blockquote p,
        .chapter-card li p,
        .chapter-card pre p {{
            text-indent: 0;
        }}

        /* 引用块 */
        .chapter-card blockquote {{
            background: var(--bg-blockquote);
            border-left: 4px solid var(--color-blockquote-border);
            margin: 20px 0;
            padding: 14px 22px;
            border-radius: 0 6px 6px 0;
            color: var(--color-text);
        }}

        .chapter-card blockquote p:last-child {{
            margin-bottom: 0;
        }}

        /* 表格 */
        .chapter-card table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.9em;
            border-radius: 6px;
            overflow: hidden;
        }}

        .chapter-card thead {{
            background: var(--bg-table-head);
        }}

        .chapter-card th {{
            padding: 10px 14px;
            text-align: left;
            font-weight: 700;
            font-family: var(--font-heading);
            color: var(--color-heading);
            border-bottom: 2px solid var(--color-border);
            white-space: nowrap;
        }}

        .chapter-card td {{
            padding: 8px 14px;
            border-bottom: 1px solid var(--color-border);
        }}

        .chapter-card tbody tr:nth-child(even) {{
            background: var(--bg-table-alt);
        }}

        .chapter-card tbody tr:hover {{
            background: #eef2f7;
        }}

        /* 列表 */
        .chapter-card ul,
        .chapter-card ol {{
            margin: 12px 0 18px 0;
            padding-left: 28px;
        }}

        .chapter-card li {{
            margin-bottom: 5px;
            line-height: 1.85;
        }}

        /* 行内代码 */
        .chapter-card code {{
            font-family: var(--font-code);
            font-size: 0.85em;
            background: var(--bg-code-inline);
            color: #c0392b;
            padding: 2px 5px;
            border-radius: 3px;
        }}

        /* 代码块 */
        .chapter-card pre {{
            background: var(--bg-code);
            border-radius: 8px;
            padding: 16px 18px;
            overflow-x: auto;
            margin: 18px 0;
            font-size: 0.82em;
            line-height: 1.6;
        }}

        .chapter-card pre code {{
            background: none;
            color: var(--color-code-text);
            padding: 0;
            font-size: inherit;
            border-radius: 0;
        }}

        /* 数学公式 */
        mjx-container {{
            font-size: 1.0em !important;
        }}

        mjx-container[display="true"] {{
            margin: 18px 0 !important;
            overflow-x: auto;
            overflow-y: hidden;
        }}

        /* 分割线 */
        .chapter-card hr {{
            border: none;
            text-align: center;
            margin: 32px 0;
        }}

        .chapter-card hr::after {{
            content: '· · ·';
            color: var(--color-gold);
            font-size: 1.2em;
            letter-spacing: 0.5em;
        }}

        /* 链接 */
        .chapter-card a {{
            color: var(--color-link);
            text-decoration: none;
            border-bottom: 1px dashed var(--color-link);
            transition: all 0.15s;
        }}

        .chapter-card a:hover {{
            color: var(--color-link-hover);
            border-bottom: 1px solid var(--color-link-hover);
        }}

        /* 图片 */
        .chapter-card img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            display: block;
            margin: 20px auto;
        }}

        /* 强调 */
        .chapter-card strong {{
            font-weight: 700;
            color: var(--color-heading);
        }}

        /* 占位文字 */
        .placeholder {{
            text-align: center;
            color: var(--color-placeholder);
            font-style: italic;
            padding: 40px;
            background: var(--bg-blockquote);
            border-radius: 8px;
        }}

        /* ============================================================
           页脚
           ============================================================ */
        .page-footer {{
            background: var(--bg-sidebar);
            border-top: 1px solid var(--color-border);
            padding: 30px 20px;
            text-align: center;
            font-size: 0.82em;
            color: var(--color-secondary);
            line-height: 1.8;
        }}

        .page-footer p {{
            margin: 4px 0;
        }}

        /* ============================================================
           回到顶部按钮
           ============================================================ */
        #back-to-top {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #d4af37 0%, #c0a062 100%);
            color: #fff;
            border: none;
            border-radius: 50%;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            z-index: 90;
            opacity: 0;
            visibility: hidden;
            transition: all var(--transition);
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        #back-to-top.visible {{
            opacity: 1;
            visibility: visible;
        }}

        #back-to-top:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
        }}

        /* ============================================================
           移动端汉堡菜单
           ============================================================ */
        #menu-toggle {{
            display: none;
            position: fixed;
            top: 14px;
            left: 14px;
            z-index: 150;
            background: var(--color-accent);
            color: #fff;
            border: none;
            border-radius: 6px;
            padding: 8px 14px;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }}

        #overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.4);
            z-index: 99;
        }}

        #overlay.visible {{
            display: block;
        }}

        /* ============================================================
           响应式
           ============================================================ */

        /* 平板端 */
        @media (max-width: 768px) {{
            :root {{
                --sidebar-width: 220px;
            }}

            .content-wrapper {{
                padding: 0 24px;
            }}

            .chapter-card {{
                padding: 28px 26px;
            }}

            .page-header h1 {{
                font-size: 1.8em;
            }}
        }}

        /* 手机端 */
        @media (max-width: 480px) {{
            :root {{
                --font-size-body: 15px;
            }}

            #menu-toggle {{
                display: block;
            }}

            #sidebar {{
                position: fixed;
                top: 0;
                left: 0;
                transform: translateX(-100%);
                width: 80%;
                max-width: 300px;
                z-index: 110;
            }}

            #sidebar.open {{
                transform: translateX(0);
            }}

            .content-wrapper {{
                padding: 0 12px;
            }}

            .chapter-card {{
                padding: 20px 16px;
                border-radius: 8px;
            }}

            .chapter-card h1 {{
                font-size: 1.5em;
            }}

            .chapter-card h2 {{
                font-size: 1.25em;
            }}

            .chapter-card h3 {{
                font-size: 1.1em;
            }}

            .chapter-card pre {{
                font-size: 0.78em;
                padding: 12px;
            }}

            .page-header {{
                padding: 50px 16px 36px;
            }}

            .page-header h1 {{
                font-size: 1.5em;
            }}

            .part-divider span {{
                font-size: 12px;
                padding: 5px 18px;
            }}
        }}

        /* 打印样式 */
        @media print {{
            #sidebar, #back-to-top, #menu-toggle, #overlay {{
                display: none !important;
            }}

            .layout {{
                display: block;
            }}

            #main {{
                padding: 0;
            }}

            .content-wrapper {{
                max-width: 100%;
                padding: 0;
            }}

            .chapter-card {{
                box-shadow: none;
                border-radius: 0;
                page-break-after: always;
            }}

            .page-header {{
                background: none;
                color: #000;
                padding: 20px 0;
            }}

            .page-header h1 {{
                -webkit-text-fill-color: #000;
                color: #000;
            }}
        }}
    </style>
</head>
<body>

    <!-- 页头 -->
    <header class="page-header">
        <h1>{escape(BOOK_TITLE)}</h1>
        <p class="subtitle">面向 A 股散户的多因子量化投资教程</p>
    </header>

    <!-- 移动端汉堡菜单 -->
    <button id="menu-toggle">☰ 目录</button>
    <div id="overlay"></div>

    <!-- 布局 -->
    <div class="layout">

        <!-- 侧边栏目录 -->
        <nav id="sidebar">
            <div class="sidebar-header">
                <h2>目 录</h2>
            </div>
            <div class="toc-nav">
                <ul>
                    {toc_html}
                </ul>
            </div>
        </nav>

        <!-- 主内容 -->
        <div id="main">
            <div class="content-wrapper" id="drag-container">
                {content_html}
                <div class="drag-handle" id="drag-handle"></div>
            </div>

            <!-- 页脚 -->
            <footer class="page-footer">
                <p><strong>{escape(BOOK_TITLE)}</strong></p>
                <p>生成日期：{gen_date}</p>
                <p>源文件：{", ".join(file_list[:5])}{"..." if len(file_list) > 5 else ""}</p>
                <p>本书内容基于 A 股（沪深 300）真实数据案例，以 Python 作为唯一编程语言</p>
            </footer>
        </div>

    </div>

    <!-- 回到顶部 -->
    <button id="back-to-top" title="回到顶部">↑</button>

    <script>
        // ============================================================
        // 移动端菜单
        // ============================================================
        var menuToggle = document.getElementById('menu-toggle');
        var sidebar = document.getElementById('sidebar');
        var overlay = document.getElementById('overlay');

        function openMenu() {{
            sidebar.classList.add('open');
            overlay.classList.add('visible');
        }}
        function closeMenu() {{
            sidebar.classList.remove('open');
            overlay.classList.remove('visible');
        }}

        menuToggle.addEventListener('click', openMenu);
        overlay.addEventListener('click', closeMenu);

        // 点击目录链接后关闭菜单
        document.querySelectorAll('#sidebar a').forEach(function(link) {{
            link.addEventListener('click', function() {{
                if (window.innerWidth <= 480) {{
                    closeMenu();
                }}
            }});
        }});

        // ============================================================
        // 回到顶部
        // ============================================================
        var backToTop = document.getElementById('back-to-top');
        window.addEventListener('scroll', function() {{
            if (window.pageYOffset > 400) {{
                backToTop.classList.add('visible');
            }} else {{
                backToTop.classList.remove('visible');
            }}
        }});
        backToTop.addEventListener('click', function() {{
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});

        // ============================================================
        // 目录高亮：滚动时自动高亮当前所在章节
        // ============================================================
        var allAnchors = {all_anchors};
        var anchorElements = allAnchors.map(function(id) {{
            return document.getElementById(id);
        }}).filter(function(el) {{ return el !== null; }});

        var tocItems = document.querySelectorAll('.toc-chapter, .toc-section, .toc-subsection');

        function highlightAnchor(id) {{
            tocItems.forEach(function(item) {{
                if (item.dataset.anchor === id) {{
                    item.classList.add('active');
                }} else {{
                    item.classList.remove('active');
                }}
            }});
        }}

        function findCurrentHeading() {{
            var bestId = null;
            var bestTop = Infinity;
            var threshold = 100; // 内容区顶部往下 100px 作为判断线

            // 找第一个"刚刚滚过顶部"的标题，它之前的那个就是当前章节
            for (var i = 0; i < anchorElements.length; i++) {{
                var top = anchorElements[i].getBoundingClientRect().top;
                if (top > threshold) {{
                    // 这个标题还在内容区下方，当前章节是它前一个
                    if (i > 0) return anchorElements[i - 1].id;
                    // 没有任何标题滚过顶部，取第一个（页面顶部）
                    return anchorElements[0].id;
                }}
            }}

            // 所有标题都已滚过顶部，当前是最后一个
            return anchorElements[anchorElements.length - 1].id;
        }}

        var scrollTimer = null;
        window.addEventListener('scroll', function() {{
            if (scrollTimer) return;
            scrollTimer = setTimeout(function() {{
                scrollTimer = null;
                var currentId = findCurrentHeading();
                if (currentId) highlightAnchor(currentId);
            }}, 150);
        }});

        // 页面加载时也运行一次
        var currentId = findCurrentHeading();
        if (currentId) highlightAnchor(currentId);

        // ============================================================
        // 拖拽调整内容区宽度
        // ============================================================
        (function() {{
            var container = document.getElementById('drag-container');
            var handle = document.getElementById('drag-handle');
            if (!container || !handle) return;

            var WIDTH_KEY = 'mfq_book_width';

            // 恢复上次的宽度
            var savedWidth = localStorage.getItem(WIDTH_KEY);
            if (savedWidth) {{
                var w = parseInt(savedWidth, 10);
                if (w >= 360) {{
                    container.style.width = w + 'px';
                }}
            }}

            var isDragging = false;
            var startX = 0;
            var startWidth = 0;

            handle.addEventListener('mousedown', function(e) {{
                isDragging = true;
                startX = e.clientX;
                startWidth = container.offsetWidth;
                document.body.style.cursor = 'ew-resize';
                document.body.style.userSelect = 'none';
                e.preventDefault();
            }});

            document.addEventListener('mousemove', function(e) {{
                if (!isDragging) return;
                var delta = e.clientX - startX;
                var newWidth = startWidth + delta;
                newWidth = Math.max(360, Math.min(newWidth, window.innerWidth * 0.95));
                container.style.width = newWidth + 'px';
            }});

            document.addEventListener('mouseup', function() {{
                if (isDragging) {{
                    isDragging = false;
                    document.body.style.cursor = '';
                    document.body.style.userSelect = '';
                    localStorage.setItem(WIDTH_KEY, container.offsetWidth);
                }}
            }});
        }})();

        // ============================================================
        // 阅读位置记忆：打开页面时自动滚动到上次离开的位置
        // ============================================================
        (function() {{
            var STORAGE_KEY = 'mfq_book_scroll';
            var saveTimer = null;

            // 页面加载时恢复位置
            var saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {{
                var pos = parseInt(saved, 10);
                if (pos > 0) {{
                    window.scrollTo(0, pos);
                    // MathJax 渲染可能导致高度变化，延迟再修正一次
                    setTimeout(function() {{ window.scrollTo(0, pos); }}, 1500);
                }}
            }}

            // 滚动时保存位置（节流：每 500ms 最多存一次）
            window.addEventListener('scroll', function() {{
                if (saveTimer) return;
                saveTimer = setTimeout(function() {{
                    saveTimer = null;
                    localStorage.setItem(STORAGE_KEY, window.scrollY);
                }}, 500);
            }});

            // 页面关闭前也存一次
            window.addEventListener('beforeunload', function() {{
                localStorage.setItem(STORAGE_KEY, window.scrollY);
            }});
        }})();
    </script>

</body>
</html>'''

    return html


if __name__ == '__main__':
    html_content = generate_html()
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    file_size = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"HTML 文件已生成: {OUTPUT_FILE}")
    print(f"文件大小: {file_size:.1f} KB")
