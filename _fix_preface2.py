# -*- coding: utf-8 -*-
filepath = "book/README.md"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old = '- **不讲纯机器学习黑箱因子**。我们用机器学习的思想（如正则化、交叉验证）来防止过拟合，但不把"丢进神经网络等结果"当作因子挖掘的正道。如果你不理解一个因子为什么有效，你就无法判断它什么时候会失效。'

new = '- **不讲纯黑箱策略**。第15章会系统讨论机器学习在量化中的应用（随机森林、XGBoost、神经网络），但我们始终坚持一个原则：ML是增强因子研究的工具，而非替代理解的捷径。即使用了ML，你仍然需要追问"模型学到了什么""它在什么条件下会失败"。'

if old in content:
    content = content.replace(old, new, 1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("OK")
else:
    print("MISS")
