和ai确认下
我发现:     "CLAUDE_CODE_EFFORT_LEVEL": "max",
这个配置非常关键, 能够大大的提升ai能力. 
类似的还有哪些? 我记得有一个配置能让ai少清理上下文, 能够把1m的空间用的更充分.



```json

{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "sk-",
    "ANTHROPIC_BASE_URL": "https://xuanji.hungrypanda.it",
    "ANTHROPIC_MODEL": "claude-opus-4-7",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-opus-4-7",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-opus-4-7",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-4-7"


//从这里复制过去

    ,"ENABLE_TOOL_SEARCH": "true",
    "CLAUDE_CODE_EFFORT_LEVEL": "max"
  },
  "contextCompactionThreshold": 0.9,
  "alwaysThinkingEnabled": true,
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "skipDangerousModePermissionPrompt": true
}

```