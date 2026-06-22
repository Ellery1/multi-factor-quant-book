# -*- coding: utf-8 -*-
"""Round 4: comprehensive quality pass on ch05/ch06."""

def patch_file(filepath, patches):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    count = 0
    for name, old, new in patches:
        if old in content:
            content = content.replace(old, new, 1)
            count += 1
            print(f"  OK: {name}")
        else:
            print(f"  MISS: {name}")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return count

total = 0

# ============================================================
# CH05 PATCHES
# ============================================================

ch05_patches = [
    # 1. Grinold citation
    (
        "Grinold citation",
        "Grinold (1989) 证明了一个优美的结果",
        'Grinold (1989) 证明了一个优美的结果（Grinold, R.C., "The Fundamental Law of Active Management," *Journal of Portfolio Management*, Vol.15, No.3, 1989, pp.30-37）'
    ),
    # 2. 5.2.4: Explain WHY Var(IC|H0)=1/(N-1)
    (
        "IC variance derivation",
        "$\\text{Var}(IC_t | H_0) = \\frac{1}{N-1} \\tag{5.9}$",
        "$\\text{Var}(IC_t | H_0) = \\frac{1}{N-1} \\tag{5.9}$\n\n" +
        "> **为什么是$1/(N-1)$？** 直觉：Spearman秩相关 = 秩的Pearson相关。当$f$和$r$独立时，两组秩就是1到$N$的两个随机排列。两个独立随机排列的Pearson相关系数的方差，由排列组合可以精确算出等于$1/(N-1)$。你可以这样记忆：如果只有$N=2$只股票，随机排名要么完全一致($IC=1$)要么完全相反($IC=-1$)，方差=1=$1/(2-1)$。股票越多，单次随机配对越难偶然产生高相关，所以方差随$N$递减。"
    ),
    # 3. Patton & Timmermann citation
    (
        "Patton-Timmermann citation",
        "**Patton & Timmermann (2010) 单调性检验**：",
        '**Patton & Timmermann (2010) 单调性检验**（Patton, A.J. & Timmermann, A., "Monotonicity in Asset Returns: New Tests with Applications to the Term Structure, the CAPM, and Portfolio Sorts," *Journal of Financial Economics*, Vol.98, No.3, 2010, pp.605-625）：'
    ),
    # 4. 5.4.3: NW worked example
    (
        "NW worked example",
        "**$L$ 怎么选？** 经验法则：",
        """**Worked Example：Newey-West调整的完整计算**

假设120个月的FM因子收益率：$\\hat{\\lambda} = 0.25\\%$，$s_{\\hat{\\beta}} = 1.1\\%$，且估计出前两阶自协方差：
- $\\hat{\\gamma}_0 = (1.1\\%)^2 = 0.000121$（即方差本身）
- $\\hat{\\gamma}_1 = 0.000040$（滞后1期自协方差，约等于$0.33\\gamma_0$——因子收益有季度惯性）
- $\\hat{\\gamma}_2 = 0.000015$（滞后2期，约$0.12\\gamma_0$）
- 更高阶接近0

取$L=2$，Bartlett核权重：$w_1 = 1-1/3 = 0.667$，$w_2 = 1-2/3 = 0.333$

$$\\widehat{\\text{Var}}_{NW} = \\frac{1}{120}[0.000121 + 2 \\times 0.667 \\times 0.000040 + 2 \\times 0.333 \\times 0.000015]$$
$$= \\frac{1}{120}[0.000121 + 0.0000533 + 0.0000100] = \\frac{0.000184}{120} = 0.00000154$$

$SE_{NW} = \\sqrt{0.00000154} = 0.124\\%$

对比不调整：$SE_{\\text{naive}} = 1.1\\%/\\sqrt{120} = 0.100\\%$

NW调整后标准误增大24%。对应$t$值从$2.50$降到$2.02$——刚好在临界值边缘！**这就是为什么NW调整可能改变你的结论**：一个看似"显著"的因子，调整后可能变成"刚好显著"甚至"不显著"。

**$L$ 怎么选？** 经验法则："""
    ),
    # 5. Shanken (1992) citation
    (
        "Shanken citation",
        "Shanken (1992) 校正可部分解决。",
        'Shanken (1992) 校正可部分解决（Shanken, J., "On the Estimation of Beta-Pricing Models," *Review of Financial Studies*, Vol.5, No.1, 1992, pp.1-33）。'
    ),
    # 6. 5.3.2: Define T explicitly
    (
        "5.3.2 define T",
        "$t_{LS} = \\frac{\\overline{r_{LS}}}{\\sigma(r_{LS}) / \\sqrt{T}} \\tag{5.13}$",
        "$t_{LS} = \\frac{\\overline{r_{LS}}}{\\sigma(r_{LS}) / \\sqrt{T}} \\tag{5.13}$\n\n" +
        "其中 $\\overline{r_{LS}}$ 是多空收益的时间序列均值，$\\sigma(r_{LS})$ 是其标准差，$T$ 是观察月数。$t_{LS} > 2$ 通常意味着多空收益在5%水平下统计显著。"
    ),
    # 7. 5.2.3: Fix formula 5.7 remnant (IR*sqrt{N}*f still there)
    (
        "5.7 formula cleanup",
        "$\\text{策略夏普比} \\approx \\frac{\\overline{IC}}{\\sigma(IC)} \\cdot \\sqrt{BR} = IR \\cdot \\sqrt{N} \\cdot f \\tag{5.7}$",
        "$\\text{策略夏普比} \\approx IR \\cdot \\sqrt{BR} \\tag{5.7}$\n\n" +
        "其中 $IR = \\overline{IC}/\\sigma(IC)$ 是信息比率，$BR$ 是有效广度（独立决策次数）。当股票间完全独立时$BR=N$（股票数量），实际中因相关性$BR < N$。"
    ),
]

n1 = patch_file("book/part2-理论篇/ch05-因子检验方法论.md", ch05_patches)
total += n1

# ============================================================
# CH06 PATCHES
# ============================================================

ch06_patches = [
    # 1. 6.4.2: Explain inner product = covariance
    (
        "inner product explanation",
        "内积 $\\langle \\cdot, \\cdot \\rangle$ 在这里是横截面协方差。",
        "内积 $\\langle \\cdot, \\cdot \\rangle$ 在这里是横截面协方差。\n\n" +
        "> **为什么用协方差当内积？** 在因子分析中，我们关心的是因子之间的\"相似度\"——如果两个因子在同一批股票上取值相似（高EP的股票BP也高），它们的协方差就大。协方差满足内积的所有数学性质（对称性、线性、正定性），所以可以直接当内积用。$\\langle f_2, g_1 \\rangle / \\langle g_1, g_1 \\rangle$ 就是$f_2$对$g_1$的\"投影系数\"——即$f_2$中有多大比例可以被$g_1$解释。"
    ),
    # 2. 6.4.3: Explain Sigma^{-1/2} intuitively
    (
        "Sigma^-1/2 intuition",
        "$\\mathbf{G} = \\mathbf{F} \\cdot \\Sigma^{-1/2} = \\mathbf{F} \\cdot \\mathbf{P} \\Lambda^{-1/2} \\mathbf{P}^T \\tag{6.17}$\n\n验证正交性",
        "$\\mathbf{G} = \\mathbf{F} \\cdot \\Sigma^{-1/2} = \\mathbf{F} \\cdot \\mathbf{P} \\Lambda^{-1/2} \\mathbf{P}^T \\tag{6.17}$\n\n" +
        "> **$\\Sigma^{-1/2}$在做什么？** 直觉上，原始因子之间有相关性——想象它们是一组不垂直的箭头。$\\Sigma^{-1/2}$的作用是把这些箭头\"掰\"成互相垂直的，而且尽量不改变每根箭头的方向（最小距离意义上的最佳旋转+缩放）。如果你熟悉PCA（主成分分析），对称正交化可以看成\"对每个主成分方向做缩放使方差归一\"——每个维度被拉伸或压缩到方差=1。\n\n" +
        "验证正交性"
    ),
    # 3. Ledoit-Wolf citation
    (
        "Ledoit-Wolf citation",
        "**Ledoit-Wolf (2004) 最优收缩**给出了在均方误差意义下最优的 $\\delta$",
        '**Ledoit-Wolf (2004) 最优收缩**（Ledoit, O. & Wolf, M., "A Well-Conditioned Estimator for Large-Dimensional Covariance Matrices," *Journal of Multivariate Analysis*, Vol.88, No.2, 2004, pp.365-411）给出了在均方误差意义下最优的 $\\delta$'
    ),
    # 4. 6.2.2: Expand proof sketch for non-math readers
    (
        "6.2.2 proof expand",
        "当 $\\boldsymbol{\\mu} = c \\cdot \\mathbf{1}$（IC全相同）且 $\\Sigma = (1-\\rho)I + \\rho \\mathbf{1}\\mathbf{1}^T$（等相关），由对称性，最优解 $\\mathbf{w}^* \\propto \\mathbf{1}$。$\\square$",
        "当 $\\boldsymbol{\\mu} = c \\cdot \\mathbf{1}$（IC全相同）且 $\\Sigma = (1-\\rho)I + \\rho \\mathbf{1}\\mathbf{1}^T$（等相关），由对称性，最优解 $\\mathbf{w}^* \\propto \\mathbf{1}$。$\\square$\n\n" +
        "> **为什么\"由对称性\"就能得到等权？** 想象一个完全对称的情景：三个因子IC一样强、两两相关性也一样。在这种情况下，没有任何理由偏好某一个因子——如果最优解给因子1权重60%、因子2权重20%，那把标签换一下（因子2叫因子1），你会得到完全不同的答案，这和\"三个因子完全等价\"矛盾。所以唯一自洽的最优解就是等权。这就像一个正三角形的重心必定在中心——因为三条边完全对称。"
    ),
]

n2 = patch_file("book/part2-理论篇/ch06-因子合成与加权.md", ch06_patches)
total += n2

print(f"\n=== TOTAL: ch05={n1}, ch06={n2}, grand total={total} ===")
