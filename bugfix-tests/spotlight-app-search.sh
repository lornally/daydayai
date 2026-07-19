#!/bin/zsh

failed=0

while IFS='|' read -r query expected_path; do
  if ! /usr/bin/mdfind "$query" | /usr/bin/grep -Fqx "$expected_path"; then
    print -u2 "FAIL: Spotlight query '$query' does not return $expected_path"
    failed=1
  fi
done <<'APPS'
Chrome|/Applications/Google Chrome.app
Visual Studio Code|/Applications/Visual Studio Code.app
keydog|/Applications/Keydog-26.7.2.app
Keynote|/Applications/Keynote.app
APPS

exit "$failed"
