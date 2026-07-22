#!/bin/zsh

failed=0

while IFS='|' read -r query expected_path; do
  if ! /usr/bin/mdfind "$query" | /usr/bin/grep -Fqx "$expected_path"; then
    print -u2 "FAIL: Spotlight query '$query' does not return $expected_path"
    failed=1
  fi
done <<'APPS'
Terminal|/System/Applications/Utilities/Terminal.app
System Settings|/System/Applications/System Settings.app
TextEdit|/System/Applications/TextEdit.app
APPS

exit "$failed"
