# AI 工具栈安装说明

目标：让 Claude Code / Codex 更少废话、更少乱写、更懂代码、更会查文档。


### Ponytail

用途：少写代码。标准库优先，删除优先，不写未来抽象。

地址：

```bash
git clone git@github.com:DietrichGebert/ponytail.git
```

用法：

```text
/ponytail ultra
```

### Caveman

用途：少说废话。把 AI 输出压短。

地址：

```bash
git clone git@github.com:JuliusBrussee/caveman.git
git clone git@github.com:yibie/caveman-codex.git
```

用法：

```text
/caveman wenyan-ultra
```

### Docs Trim

用途：文档瘦身。单点维护、简洁优先、禁代码、用案例讲。

本仓库自带：

```text
docs-trim/SKILL.md
```

用法：

```text
Use docs-trim. 只改文档，禁改代码。
```

### Bugfix Protocol

用途：修 bug 时强制文档 -> 红测 -> 最小修 -> 绿停。

本仓库自带：

```text
bugfix-protocol/SKILL.md
```

用法：

```text
Use bugfix-protocol. 未红禁改源码。
```

### Serena

用途：语义级读代码。查符号、引用、实现、诊断，比纯搜索稳。

地址：

```bash
git clone git@github.com:oraios/serena.git
```

脚本会配置 MCP：

- Claude Code：`serena start-mcp-server --context claude-code --project-from-cwd`
- Codex：`serena start-mcp-server --project-from-cwd --context=codex`

用法：

```text
Use Serena to inspect symbols/references before editing.
```

### Context7

用途：查最新第三方库/API 文档，避免 AI 用旧 API。

地址：

```bash
git clone git@github.com:upstash/context7.git
```

脚本会配置：

- Claude Code：Context7 HTTP MCP
- Codex：Context7 stdio MCP
- Context7 skill

用法：

```text
use context7 for Next.js middleware docs
use context7 with /vercel/next.js for app router setup
```

## 验证

Claude Code：

```bash
claude plugin list
claude mcp get serena
claude mcp get context7
```

Codex：

```bash
codex mcp get serena
codex mcp get context7
```

在聊天里：

```text
/plugins
/mcp
```

## 日常提示词

写代码：

```text
/ponytail ultra
/caveman wenyan-ultra
最小修。绿即止。
```

改文档：

```text
Use docs-trim.
/caveman wenyan-ultra
只改文档，禁改代码。
```

修 bug：

```text
Use bugfix-protocol.
/ponytail ultra
/caveman wenyan-ultra
文档 -> 红测 -> 最小修 -> 绿停。
```

查库文档：

```text
use context7 for <库名> <问题>
```

读代码：

```text
Use Serena to find the relevant symbols and references first.
```

## 可选研究项

这些不是默认栈。想研究再装。

### code-hacker

用途：一套 MCP/agent 工具箱。偏实验，不建议直接接生产工作区。

地址：

```bash
git clone git@github.com:hackerlibs/code-hacker.git
```

建议：先读 `install.sh` 和 `start_servers.sh`，再决定是否运行。

### Hermes Agent

用途：agent harness。可当另一个长期运行的个人 agent 系统。

地址：

```bash
git clone git@github.com:nousresearch/hermes-agent.git
```

建议：单独试，不和默认栈混装。

## 常见问题

### Serena 一直弹浏览器

关闭自动打开 dashboard：

```yaml
web_dashboard_open_on_launch: false
```

位置：

```text
~/.serena/serena_config.yml
```

本仓库脚本已自动处理。

### Context7 需要 key 吗

不必须。无 key 可用，限额低。

需要更高限额时设置：

```bash
export CONTEXT7_API_KEY='ctx7sk_...'
```

### Codex 找不到 plugin 命令

有些 Codex CLI 版本没有 plugin 子命令。脚本会尝试找 VS Code 插件里的 Codex 二进制。

如果仍失败，至少 skills 和 MCP 仍可用。
