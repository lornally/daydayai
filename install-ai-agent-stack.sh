#!/usr/bin/env bash
set -euo pipefail

PROJECT="${1:-$PWD}"
TOOLS_DIR="${TOOLS_DIR:-$HOME/AI/参考工具}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PATH="$HOME/.local/bin:$HOME/.nvm/versions/node/v24.13.0/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "missing command: $1" >&2
    return 1
  }
}

run() {
  echo "+ $*"
  "$@"
}

try() {
  echo "+ $*"
  "$@" || echo "skip: $*"
}

codex_with_plugin() {
  local c
  while IFS= read -r c; do
    "$c" plugin marketplace --help >/dev/null 2>&1 && {
      printf '%s\n' "$c"
      return 0
    }
  done < <(which -a codex 2>/dev/null | awk '!seen[$0]++')

  for c in "$HOME"/.vscode/extensions/openai.chatgpt-*/bin/*/codex; do
    [[ -x "$c" ]] || continue
    "$c" plugin marketplace --help >/dev/null 2>&1 && {
      printf '%s\n' "$c"
      return 0
    }
  done

  return 1
}

clone_or_update() {
  local repo="$1" dir="$2"
  if [[ -d "$dir/.git" ]]; then
    try git -C "$dir" pull --ff-only
  else
    mkdir -p "$(dirname "$dir")"
    run git clone "$repo" "$dir"
  fi
}

install_skill_file() {
  local src="$1" dst_root="$2" name="$3"
  [[ -f "$src" ]] || return 0
  mkdir -p "$dst_root/$name"
  cp "$src" "$dst_root/$name/SKILL.md"
  echo "installed skill: $dst_root/$name"
}

install_bugfix_protocol() {
  local src="$ROOT/bugfix-protocol/SKILL.md"
  [[ -f "$src" ]] || return 0
  install_skill_file "$src" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills" bugfix-protocol
  install_skill_file "$src" "${CODEX_HOME:-$HOME/.codex}/skills" bugfix-protocol
  [[ -d "$PROJECT" ]] && install_skill_file "$src" "$PROJECT/.agents/skills" bugfix-protocol
}

install_context7_skill() {
  local src="$TOOLS_DIR/context7/skills/context7-mcp/SKILL.md"
  install_skill_file "$src" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills" context7-mcp
  install_skill_file "$src" "${CODEX_HOME:-$HOME/.codex}/skills" context7-mcp
  [[ -d "$PROJECT" ]] && install_skill_file "$src" "$PROJECT/.agents/skills" context7-mcp
}

install_docs_trim() {
  local src="$ROOT/docs-trim/SKILL.md"
  [[ -f "$src" ]] || return 0
  install_skill_file "$src" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills" docs-trim
  install_skill_file "$src" "${CODEX_HOME:-$HOME/.codex}/skills" docs-trim
  [[ -d "$PROJECT" ]] && install_skill_file "$src" "$PROJECT/.agents/skills" docs-trim
}

disable_serena_dashboard_autopen() {
  local cfg="$HOME/.serena/serena_config.yml"
  [[ -f "$cfg" ]] || return 0
  if grep -q '^web_dashboard_open_on_launch:' "$cfg"; then
    perl -0pi -e 's/^web_dashboard_open_on_launch:.*/web_dashboard_open_on_launch: false/m' "$cfg"
  else
    printf '\nweb_dashboard_open_on_launch: false\n' >> "$cfg"
  fi
  echo "updated: $cfg"
}

install_claude_plugins() {
  need claude || return 0
  try claude plugin marketplace add DietrichGebert/ponytail
  try claude plugin install ponytail@ponytail --scope user
  try claude plugin enable ponytail@ponytail

  try claude plugin marketplace add JuliusBrussee/caveman
  try claude plugin install caveman@caveman --scope user
  try claude plugin enable caveman@caveman
}

install_codex_ponytail() {
  local c
  if c="$(codex_with_plugin)"; then
    try "$c" plugin marketplace add DietrichGebert/ponytail
    try "$c" plugin add ponytail@ponytail
  fi

  need npx || return 0
  NPM_CONFIG_CACHE="${NPM_CONFIG_CACHE:-/tmp/ponytail-npm-cache}" \
    try npx -y skills add DietrichGebert/ponytail --skill '*' -a codex --yes
}

install_codex_caveman() {
  need npx || return 0
  NPM_CONFIG_CACHE="${NPM_CONFIG_CACHE:-/tmp/caveman-npm-cache}" \
    try npx -y skills add JuliusBrussee/caveman --skill '*' -a codex --yes

  local installer="$TOOLS_DIR/caveman-codex/install.sh"
  if [[ -x "$installer" || -f "$installer" ]]; then
    try bash "$installer" --project "$PROJECT" --force --no-prompt
  fi
}

remove_mcp() {
  local client="$1" name="$2"
  if "$client" mcp get "$name" >/dev/null 2>&1; then
    try "$client" mcp remove "$name"
  fi
}

install_claude_mcp() {
  need claude || return 0
  need uvx || return 0

  remove_mcp claude serena
  try claude mcp add --scope user serena -- \
    "$(command -v uvx)" --from git+https://github.com/oraios/serena \
    serena start-mcp-server --context claude-code --project-from-cwd

  remove_mcp claude context7
  if [[ -n "${CONTEXT7_API_KEY:-}" ]]; then
    try claude mcp add --scope user --transport http context7 \
      -H "CONTEXT7_API_KEY: $CONTEXT7_API_KEY" \
      https://mcp.context7.com/mcp
  else
    try claude mcp add --scope user --transport http context7 \
      https://mcp.context7.com/mcp
  fi
}

install_codex_mcp() {
  need codex || return 0
  need uvx || return 0
  need npx || return 0

  remove_mcp codex serena
  try codex mcp add serena -- \
    "$(command -v uvx)" --from git+https://github.com/oraios/serena \
    serena start-mcp-server --project-from-cwd --context=codex

  remove_mcp codex context7
  if [[ -n "${CONTEXT7_API_KEY:-}" ]]; then
    try codex mcp add context7 \
      --env "PATH=$(dirname "$(command -v npx)"):$PATH" \
      --env "NPM_CONFIG_CACHE=/tmp/context7-npm-cache" \
      --env "CONTEXT7_API_KEY=$CONTEXT7_API_KEY" -- \
      "$(command -v npx)" -y @upstash/context7-mcp
  else
    try codex mcp add context7 \
      --env "PATH=$(dirname "$(command -v npx)"):$PATH" \
      --env "NPM_CONFIG_CACHE=/tmp/context7-npm-cache" -- \
      "$(command -v npx)" -y @upstash/context7-mcp
  fi
}

main() {
  [[ -d "$PROJECT" ]] || { echo "project not found: $PROJECT" >&2; exit 1; }

  clone_or_update git@github.com:JuliusBrussee/caveman.git "$TOOLS_DIR/caveman"
  clone_or_update git@github.com:yibie/caveman-codex.git "$TOOLS_DIR/caveman-codex"
  clone_or_update git@github.com:oraios/serena.git "$TOOLS_DIR/serena"
  clone_or_update git@github.com:upstash/context7.git "$TOOLS_DIR/context7"

  install_bugfix_protocol
  install_docs_trim
  install_context7_skill
  disable_serena_dashboard_autopen
  install_claude_plugins
  install_codex_ponytail
  install_codex_caveman
  install_claude_mcp
  install_codex_mcp

  echo
  echo "done. Restart Claude Code / Codex / VS Code."
  echo "verify in agent: /plugins, /mcp"
}

main "$@"
