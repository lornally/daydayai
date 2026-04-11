截至 **2026-04-09**，**Typora 基本可以认为“不支持 Typst 原生编辑/渲染”**。

官方依据是：

- Typora 现在仍定位为 **Markdown 编辑器**，官网功能列表里是 Markdown、数学、Mermaid、导出等，没有列出 Typst 文档支持。
- Typora 的数学功能官方写得很明确：**用 TeX/LaTeX 语法，由 MathJax 渲染**。
- 导出这块官方主要是 PDF / HTML / Image，其他很多格式走 Pandoc，也没看到 Typst 作为原生编辑格式。

所以更准确地说：
- **支持 LaTeX 风格公式**：`$...$` / `$$...$$`
- **不等于支持 Typst 文档**：`.typ` 那套语法、版面规则、编译流程，不是 Typora 的主场

如果你想认真写 Typst，**更推荐直接用 Typst 官方 web app 或本地 `typst` 编译器**。

**Typst 是什么**
它可以理解成：**“更现代、更统一、更快的 LaTeX 替代方案之一”**。

对 LaTeX 用户最直观的几个点：

1. **语法更轻**
   - 没那么多 `\begin{...}` / `\end{...}`
   - 常见结构更像 Markdown

2. **编译很快**
   - 官方强调通常是毫秒级，适合实时预览

3. **内置能力更多**
   - 很多 LaTeX 里要靠包的东西，Typst 里是内建函数/规则

4. **样式系统更统一**
   - 它不是一堆历史包拼起来的感觉
   - 主要靠 `set` / `show` 规则控制排版

5. **数学思路类似，但语法不是 LaTeX 兼容层**
   - 会有相似感
   - 但不是“把 `.tex` 原封不动搬过去就能跑”

**怎么用**
最简单两种：

1. **用官方 web app**
   - 直接浏览器里写，所见即所得预览很顺
2. **装本地编译器**
   - 写 `hello.typ`
   - 用 `typst watch hello.typ`
   - 它会实时生成 PDF

**给你一个 LaTeX -> Typst 的对照感**
LaTeX：

```tex
\section{Introduction}
Einstein gave us
\[
E = mc^2
\]
```

$$
\section{Introduction}
Einstein gave us

E = mc^2


$$

Typst：

```typ
= Introduction

Einstein gave us

$ E = m c^2 $
```

再看一个“图片 + 标题 + 引用”：

```typ
#figure(
  image("fig.png", width: 70%),
  caption: [A sample figure],
) <fig1>

See @fig1.
```

**Typst 的几个核心语法观念**
- 普通正文：直接写
- 标题：`= 一级标题`，`== 二级标题`
- 列表：`-` 或 `+`
- 数学：`$...$`
- 调函数：`#something(...)`
- 设样式：`#set ...`
- 规则改写：`#show ...`

**如果你之前主要用 LaTeX，你会喜欢 Typst 的地方**
- 写文档更顺手
- 模板和排版逻辑更清晰
- 中文处理通常更省心
- 参考文献、图片、交叉引用这些都比较现代化

**但也要有预期**
- 生态还没有 LaTeX 那么老辣
- 某些超细分学术模板、冷门包、TikZ 级别积累，LaTeX 还是更强
- 如果你的学校/期刊只给 `.cls` / `.sty`，那很多时候还是得回 LaTeX

**我的建议**
- **做笔记/Markdown 写作**：继续 Typora
- **做正式排版文档**：试 Typst
- **投论文、必须套现成 LaTeX 模板**：LaTeX 先别丢

来源：
- Typora 功能页: https://typora.io/
- Typora 数学文档: https://support.typora.io/Math/
- Typora 导出文档: https://support.typora.io/Export/
- Typst 总文档: https://typst.app/docs/
- Typst 写作教程: https://typst.app/docs/tutorial/writing-in-typst/
- Typst 给 LaTeX 用户的指南: https://typst.app/docs/guides/guide-for-latex-users/
- Typst 开源/CLI 说明: https://typst.app/open-source/
- Typst PDF/命令行导出: https://typst.app/docs/reference/pdf/

如果你愿意，我下一条可以直接给你一份：
1. **“LaTeX 用户 10 分钟上手 Typst” cheat sheet**
2. **论文模板级的 Typst 最小示例**
3. **LaTeX 和 Typst 常用语法对照表**