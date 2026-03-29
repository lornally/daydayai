#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="${1:-$HOME/Downloads}"
OUTPUT_DIR="${2:-$INPUT_DIR/utf8}"

INPUT_DIR="${INPUT_DIR%/}"
OUTPUT_DIR="${OUTPUT_DIR%/}"

converted=0
skipped=0
failed=0

if [[ ! -d "$INPUT_DIR" ]]; then
  printf '输入目录不存在: %s\n' "$INPUT_DIR" >&2
  exit 1
fi

if [[ "$OUTPUT_DIR" == "$INPUT_DIR" ]]; then
  printf '输出目录不能和输入目录相同: %s\n' "$OUTPUT_DIR" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

is_utf8() {
  iconv -f UTF-8 -t UTF-8 "$1" >/dev/null 2>&1
}

looks_like_text() {
  local desc
  desc=$(file -b "$1" 2>/dev/null || true)
  case "$desc" in
    *text*|*empty*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

convert_one() {
  local src="$1"
  local rel dst tmp

  if [[ "$src" == "$OUTPUT_DIR"/* ]]; then
    return 0
  fi

  if ! looks_like_text "$src"; then
    skipped=$((skipped + 1))
    printf '跳过(非文本): %s\n' "$src"
    return 0
  fi

  if is_utf8 "$src"; then
    skipped=$((skipped + 1))
    printf '跳过(已是UTF-8): %s\n' "$src"
    return 0
  fi

  rel="${src#$INPUT_DIR/}"
  dst="$OUTPUT_DIR/$rel"

  mkdir -p "$(dirname "$dst")"
  tmp="$dst.tmp.$$"

  if iconv -f GB18030 -t UTF-8 "$src" > "$tmp" 2>/dev/null; then
    mv "$tmp" "$dst"
    converted=$((converted + 1))
    printf '已转换: %s -> %s\n' "$src" "$dst"
  else
    rm -f "$tmp"
    failed=$((failed + 1))
    printf '转换失败: %s\n' "$src" >&2
  fi
}

while IFS= read -r -d '' src; do
  convert_one "$src"
done < <(
  find "$INPUT_DIR" \
    \( -path "$OUTPUT_DIR" -o -path "$OUTPUT_DIR/*" \) -prune -o \
    -type f -print0
)

printf '\n完成: converted=%d skipped=%d failed=%d\n' "$converted" "$skipped" "$failed"
printf '输出目录: %s\n' "$OUTPUT_DIR"
