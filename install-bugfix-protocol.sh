#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$ROOT/bugfix-protocol/SKILL.md"
PROJECT="${1:-$PWD}"

if [[ ! -f "$SRC" ]]; then
  echo "missing: $SRC" >&2
  exit 1
fi

install_skill() {
  local dir="$1"
  mkdir -p "$dir/bugfix-protocol"
  cp "$SRC" "$dir/bugfix-protocol/SKILL.md"
  echo "installed: $dir/bugfix-protocol/SKILL.md"
}

install_skill "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
install_skill "${CODEX_HOME:-$HOME/.codex}/skills"

if [[ -d "$PROJECT" ]]; then
  install_skill "$PROJECT/.agents/skills"
fi

echo "restart Claude Code / Codex to pick up new skill."
