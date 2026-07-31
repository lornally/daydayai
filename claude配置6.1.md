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



### 7.31
* 你看下文档, claude的opus4.6有这些可以优化的配置. fable5有吗? 1m上下文怎么打开?

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "sk-",
    "ANTHROPIC_BASE_URL": "https://xuanji.hungrypanda.it",
    "ANTHROPIC_MODEL": "claude-fable-5",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-fable-5",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-fable-5",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-fable-5",
    "ANTHROPIC_DEFAULT_FABLE_MODEL": "claude-fable-5",
    "ENABLE_TOOL_SEARCH": "true",

    "CLAUDE_CODE_EFFORT_LEVEL": "max",

    "DISABLE_AUTO_COMPACT": "1"

  },
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "skipDangerousModePermissionPrompt": true
}
```

* 别人和我说, 因为我用的是第三方的服务, 因此cc-switch要加上1m开关, 不然claude code会误判上下文, 我这边现在的症状是, vscode里面的claude code插件说2句话就上下文紧张了, 比如咱们这个对话就已经上下文紧张了.

* claude在胡说八道, 升级cc-switch之后, 问题解决.