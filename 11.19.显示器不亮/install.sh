#!/bin/zsh
# install.sh — 一次性安装: 修复脚本 + 自动看护
#
# 用法: ./install.sh      (每台机器只需执行一次)
# 之后: 显示器每次从休眠唤醒后自动检测, 卡死会自动修复;
#       也可随时手动执行 fix-wescom.
#
# 详细说明见同目录 README.md.

set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.local/bin"
AGENTS="$HOME/Library/LaunchAgents"
LABEL="com.user.wescom-watchdog"
PLIST="$AGENTS/$LABEL.plist"

echo "==> 平台: $(uname -m) / macOS $(sw_vers -productVersion)"

if ! command -v brew >/dev/null 2>&1; then
  echo "ERROR: 未找到 Homebrew。请先安装 https://brew.sh 后重跑本脚本。"
  echo "       国内网络可能需要先挂代理。"
  exit 1
fi

echo "==> 安装依赖: displayplacer, DDC 工具"
command -v displayplacer >/dev/null 2>&1 || brew install displayplacer
if [[ "$(uname -m)" == "arm64" ]]; then
  command -v m1ddc >/dev/null 2>&1 || brew install m1ddc
else
  command -v ddcctl >/dev/null 2>&1 || brew install ddcctl
fi

echo "==> 安装脚本到 $BIN"
mkdir -p "$BIN"
install -m 755 "$HERE/fix-wescom"      "$BIN/fix-wescom"
install -m 755 "$HERE/wescom-watchdog" "$BIN/wescom-watchdog"

echo "==> 编译软件重连工具 wescom-dpfix (私有 SkyLight 接口)"
if command -v clang >/dev/null 2>&1 && \
   clang -O2 -Wall -framework CoreGraphics "$HERE/wescom-dpfix.c" -o "$BIN/wescom-dpfix" 2>/tmp/wescom-build.log; then
  chmod 755 "$BIN/wescom-dpfix"
else
  echo "WARN: wescom-dpfix 编译失败（需要 Xcode Command Line Tools）。"
  echo "      仍会安装 DDC/刷新率/物理拔插方案；编译日志: /tmp/wescom-build.log"
fi

echo "==> 安装自动看护服务 ($LABEL)"
mkdir -p "$AGENTS"
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
    <string>/tmp/wescom-watchdog.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/wescom-watchdog.log</string>
</dict>
</plist>
PLIST_EOF

launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
if ! launchctl bootstrap "gui/$(id -u)" "$PLIST" ; then
  sleep 1
  launchctl bootout "gui/$(id -u)/$LABEL" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
fi

echo
echo "完成 ✅  (以后无需再运行本脚本)"
echo "  手动修复:      $BIN/fix-wescom     (若 $BIN 不在 PATH 里就用完整路径)"
echo "  自动看护日志:  /tmp/wescom-watchdog.log"
echo "  卸载:          launchctl bootout gui/$(id -u)/$LABEL && rm '$PLIST' '$BIN/fix-wescom' '$BIN/wescom-watchdog'"
