#!/bin/zsh
# install-os27.sh — 在 os27 上安装专用看护（只检测 + 通知）
# 不改仓库里 os15 的共享脚本（../fix-wescom、../wescom-watchdog 保持原样）。
#
# 本机旧名字 fix-wescom / wescom-watchdog 也会指向 os27 版本，
# 避免在这台机器上误跑 os15 的逻辑。

set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.local/bin"
AGENTS="$HOME/Library/LaunchAgents"
LABEL="com.user.wescom-watchdog"
PLIST="$AGENTS/$LABEL.plist"

mkdir -p "$BIN" "$AGENTS"
install -m 755 "$HERE/fix-wescom-os27" "$BIN/fix-wescom-os27"
install -m 755 "$HERE/wescom-watchdog-os27" "$BIN/wescom-watchdog-os27"
install -m 755 "$HERE/fix-wescom-os27" "$BIN/fix-wescom"
install -m 755 "$HERE/wescom-watchdog-os27" "$BIN/wescom-watchdog"

cat > "$PLIST" <<'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.wescom-watchdog</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/zsh</string>
        <string>-c</string>
        <string>exec "$HOME/.local/bin/wescom-watchdog"</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/wescom-watchdog-os27.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/wescom-watchdog-os27.log</string>
</dict>
</plist>
PLIST_EOF

launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

echo "os27 看护已安装并启动。"
echo "  日志: /tmp/wescom-watchdog-os27.log"
echo "  手动诊断: $BIN/fix-wescom-os27"
echo "  只检测+通知，不会动分辨率/布局/主屏。"
