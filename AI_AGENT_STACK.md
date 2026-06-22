# AI Agent Stack

安装：

- Ponytail：少写代码。
- Caveman：少说废话。
- Bugfix Protocol：文档 -> 红测 -> 最小修 -> 绿停。
- Docs Trim：文档瘦身。
- Serena MCP：语义级读代码。
- Context7 MCP/skill：查最新库文档。

## 安装

在本仓库运行：

```bash
chmod +x install-ai-agent-stack.sh
./install-ai-agent-stack.sh /path/to/your/project
```

可选：Context7 key。

```bash
export CONTEXT7_API_KEY='ctx7sk_...'
./install-ai-agent-stack.sh /path/to/your/project
```

无 key 也能用，限额低。

工具默认 clone/更新到：

```text
$TOOLS_DIR
```

默认值：

```text
~/AI/参考工具
```

指定目录：

```bash
TOOLS_DIR="$HOME/AI/tools" ./install-ai-agent-stack.sh /path/to/project
```

## 写入位置

Claude Code：

- `~/.claude/skills/bugfix-protocol`
- `~/.claude/skills/docs-trim`
- `~/.claude/skills/context7-mcp`
- 插件：`ponytail`、`caveman`
- MCP：`serena`、`context7`

Codex：

- `~/.codex/skills/bugfix-protocol`
- `~/.codex/skills/docs-trim`
- `~/.codex/skills/context7-mcp`
- 插件：`ponytail`
- Caveman skills
- MCP：`serena`、`context7`

项目：

- `.agents/skills/bugfix-protocol`
- `.agents/skills/docs-trim`
- `.agents/skills/context7-mcp`
- `.agents/skills/caveman*`
- `.agents/skills/ponytail*`
- `.codex-plugins/caveman`

## 用法

风格：

```text
/ponytail ultra
/caveman wenyan-ultra
```

文档：

```text
Use docs-trim. 只改文档。单点维护。简洁优先。文档禁代码。用案例讲。
```

修 bug：

```text
Use bugfix-protocol. 文档短，无代码，用案例讲 bug。文档 -> 红测 -> 最小修 -> 绿停。
```

查外部库文档：

```text
use context7 for Next.js middleware docs
use context7 with /vercel/next.js for app router setup
```

读代码结构：

```text
Use Serena to inspect symbols/references before editing.
```

## 验证

Claude Code：

```text
/plugins
/mcp
```

Codex：

```text
/mcp
```

命令行：

```bash
claude plugin list
claude mcp get serena
claude mcp get context7
codex mcp get serena
codex mcp get context7
```

## 注意

- 安装后重启 Claude Code、Codex、VS Code。
- Serena 通过 `uvx` 启动，首次可能慢。
- Serena dashboard 保留，但不自动弹浏览器。
- Claude Code 的 Context7 用 HTTP MCP。
- Codex 的 Context7 用 stdio MCP，避免安装时卡 OAuth。
- 脚本不保存 key；除非你先导出 `CONTEXT7_API_KEY`。
