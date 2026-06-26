# -*- coding: utf-8 -*-
"""Convert inline citations to [n] footnote + chapter-end references for ch05/ch10/ch11/ch12."""
import os

def fix_file(filepath, replacements, new_refs=None):
    """replacements: list of (old, new) tuples. new_refs: text to add/update in references section."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    changed = False
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new, 1)
            changed = True
            print(f"  OK: {filepath.split('/')[-1]}: {old[:50]}...")
        else:
            print(f"  MISS: {filepath.split('/')[-1]}: {old[:50]}...")

    # Add references section if needed
    if new_refs and changed:
        if '## 参考文献' in content:
            # Append to existing references
            ref_idx = content.find('## 参考文献')
            # Find end of references section (next --- or end of file)
            ref_end = content.find('\n---', ref_idx + 10)
            if ref_end < 0:
                ref_end = len(content)
            # Check if ref already exists
            existing_refs = content[ref_idx:ref_end]
            for ref_line in new_refs.split('\n'):
                if ref_line.strip() and ref_line.strip() not in existing_refs:
                    content = content[:ref_end] + '\n' + ref_line + '\n' + content[ref_end:]
        else:
            # Add new references section before the last ---
            last_hr = content.rfind('\n---')
            if last_hr > 0:
                content = content[:last_hr] + '\n\n## 参考文献\n\n' + new_refs + '\n' + content[last_hr:]
            else:
                content += '\n\n## 参考文献\n\n' + new_refs + '\n'

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    return changed

# ============================================================
# CH05: Shanken inline → [7] footnote
# ============================================================
fix_file(
    "book/part2-理论篇/ch05-因子检验方法论.md",
    [
        (
            'Shanken (1992) 校正可部分解决（Shanken, J., "On the Estimation of Beta-Pricing Models," *Review of Financial Studies*, Vol.5, No.1, 1992, pp.1-33）。',
            'Shanken (1992) 校正可部分解决[7]。'
        ),
    ],
    '>[7] Shanken, J., "On the Estimation of Beta-Pricing Models," *Review of Financial Studies*, Vol.5, No.1, 1992, pp.1-33.'
)

# ============================================================
# CH10: Bailey & Lopez de Prado inline → [1] footnote
# ============================================================
fix_file(
    "book/part4-进阶篇/ch10-过拟合与陷阱.md",
    [
        (
            'Bailey & Lopez de Prado (2014) ("The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality," *Journal of Portfolio Management*, Vol.40, No.5, 2014, pp.94-107) 提出了一个优雅的校正方法',
            'Bailey & Lopez de Prado (2014)[1] 提出了一个优雅的校正方法'
        ),
    ],
    '>[1] Bailey, D.H. & López de Prado, M.M., "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality," *Journal of Portfolio Management*, Vol.40, No.5, 2014, pp.94-107.'
)

# ============================================================
# CH11: Almgren & Chriss inline → [1] footnote
# ============================================================
fix_file(
    "book/part4-进阶篇/ch11-从回测到实盘.md",
    [
        (
            '> 参考：Almgren, R. & Chriss, N. (2000). "Optimal Execution of Portfolio Transactions." *Journal of Risk*, Vol.3, No.2, pp.5-39.这是散户的巨大优势！',
            '> 这是散户的巨大优势[1]！'
        ),
    ],
    '>[1] Almgren, R. & Chriss, N., "Optimal Execution of Portfolio Transactions," *Journal of Risk*, Vol.3, No.2, 2000, pp.5-39.'
)

# ============================================================
# CH12: Gu, Kelly & Xiu inline → [1] footnote
# ============================================================
fix_file(
    "book/part4-进阶篇/ch12-前沿方向与延伸阅读.md",
    [
        (
            '学术研究（如Gu, Kelly & Xiu 2020, "Empirical Asset Pricing via Machine Learning," *Review of Financial Studies*, 33(5), 2020, pp.2223-2273）发现',
            '学术研究（如Gu, Kelly & Xiu 2020[1]）发现'
        ),
    ],
    '>[1] Gu, S., Kelly, B. & Xiu, D., "Empirical Asset Pricing via Machine Learning," *Review of Financial Studies*, Vol.33, No.5, 2020, pp.2223-2273.'
)

print("\nDone. Now regenerating HTML...")
