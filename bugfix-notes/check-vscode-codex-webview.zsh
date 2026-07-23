#!/bin/zsh

set -eu

code_data="$HOME/Library/Application Support/Code"
workspace_id=""

for workspace_file in "$code_data"/User/workspaceStorage/*/workspace.json; do
  if rg -q '"folder"[[:space:]]*:[[:space:]]*"file:///Users/X/AI/deep"' "$workspace_file"; then
    workspace_id="${workspace_file:h:t}"
    break
  fi
done

if [[ -z "$workspace_id" ]]; then
  print -u2 "FAIL: deep workspace state was not found"
  exit 1
fi

codex_log=""
for exthost_log in "$code_data"/logs/*/window*/exthost/exthost.log; do
  if rg -q "workspaceStorage/$workspace_id" "$exthost_log"; then
    candidate="${exthost_log:h}/openai.chatgpt/Codex.log"
    if [[ -f "$candidate" && ( -z "$codex_log" || "$candidate" -nt "$codex_log" ) ]]; then
      codex_log="$candidate"
    fi
  fi
done

if [[ -z "$codex_log" ]]; then
  print -u2 "FAIL: deep Codex log was not found"
  exit 1
fi

last_initialize=$(rg -n 'Initialize received id=1' "$codex_log" | tail -n 1 | cut -d: -f1)
if [[ -z "$last_initialize" ]]; then
  print -u2 "FAIL: Codex backend did not initialize"
  exit 1
fi

if ! tail -n "+$last_initialize" "$codex_log" | rg -q 'ready provider mounted.*windowType=extension'; then
  print -u2 "FAIL: Codex Webview did not mount after backend initialization"
  exit 1
fi

print "PASS: Codex Webview mounted after backend initialization"
