# AI Agent Stack

Installs:

- Ponytail: minimal-code mode.
- Caveman: terse-output mode.
- Bugfix Protocol: doc -> red test -> minimal fix -> green stop.
- Serena MCP: semantic code tools.
- Context7 MCP/skill: current library docs.

## Install

From this repo:

```bash
chmod +x install-ai-agent-stack.sh
./install-ai-agent-stack.sh /path/to/your/project
```

Optional Context7 key:

```bash
export CONTEXT7_API_KEY='ctx7sk_...'
./install-ai-agent-stack.sh /path/to/your/project
```

No key also works, with lower rate limits.

The script clones/upgrades tools under:

```text
$TOOLS_DIR
```

Default:

```text
~/AI/参考工具
```

Override:

```bash
TOOLS_DIR="$HOME/AI/tools" ./install-ai-agent-stack.sh /path/to/project
```

## What It Writes

Claude Code:

- `~/.claude/skills/bugfix-protocol`
- `~/.claude/skills/context7-mcp`
- Claude plugins: `ponytail`, `caveman`
- MCP servers: `serena`, `context7`

Codex:

- `~/.codex/skills/bugfix-protocol`
- `~/.codex/skills/context7-mcp`
- Codex plugin: `ponytail`
- Codex Caveman skills via `skills add`
- MCP servers: `serena`, `context7`

Project:

- `.agents/skills/bugfix-protocol`
- `.agents/skills/context7-mcp`
- `.agents/skills/caveman*` when Caveman Codex installer is available
- `.codex-plugins/caveman` when Caveman Codex installer is available

## Use

Style:

```text
/ponytail ultra
/caveman wenyan-ultra
```

Bug fix:

```text
Use bugfix-protocol. 文档短，无代码，用案例讲 bug。文档 -> 红测 -> 最小修 -> 绿停。
```

Docs:

```text
use context7 for Next.js middleware docs
use context7 with /vercel/next.js for app router setup
```

Semantic code:

```text
Use Serena to inspect symbols/references before editing.
```

## Verify

Claude Code:

```text
/plugins
/mcp
```

Codex:

```text
/mcp
```

Shell:

```bash
claude plugin list
claude mcp get serena
claude mcp get context7
codex mcp get serena
codex mcp get context7
```

## Notes

- Restart Claude Code, Codex, and VS Code after install.
- Serena starts through `uvx`; first launch may be slow.
- Serena dashboard stays enabled but no longer auto-opens browser tabs.
- Context7 uses hosted HTTP MCP for Claude Code.
- Context7 uses stdio MCP for Codex to avoid OAuth blocking in terminal install.
- Script stores no API keys unless `CONTEXT7_API_KEY` is already exported.
