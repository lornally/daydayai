#!/bin/bash
#
# unfuck_macos.sh  --claude
# 关闭 macOS 各种反人类的自动行为
# 每次系统更新后如果设置被重置，重新跑一遍即可
#

echo "开始关闭 macOS 反人类设置..."

# ============================================================
# 文本输入相关
# ============================================================

# 关闭自动修正（把你打的字偷偷改成别的）
defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false

# 关闭智能引号（自动把 "直引号" 变成 "弯引号"）
defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false

# 关闭智能破折号（自动把 -- 变成 —）
defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false

# 关闭首字母自动大写
defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false

# 关闭双空格自动变句号
defaults write NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false

# 关闭文本替换（自动把缩写展开成完整文本）
defaults write NSGlobalDomain WebAutomaticTextReplacementEnabled -bool false

# 关闭拼写检查自动标红
defaults write NSGlobalDomain NSAutomaticTextCompletionEnabled -bool false

# 关闭内联预测文本（打字时灰色的建议文字）
defaults write NSGlobalDomain NSAutomaticInlinePredictionEnabled -bool false

# ============================================================
# 窗口管理相关（Sequoia 的平铺功能）
# ============================================================

# 关闭拖动窗口到屏幕边缘自动平铺
defaults write com.apple.WindowManager EnableTilingByEdgeDrag -bool false

# 关闭拖动窗口到菜单栏自动最大化
defaults write com.apple.WindowManager EnableTilingOptionAccelerator -bool false

# 关闭拖动到顶部边缘平铺
defaults write com.apple.WindowManager EnableTopTilingByEdgeDrag -bool false

# ============================================================
# 程序坞（Dock）相关
# ============================================================

# 关闭最近使用的应用显示在 Dock 里
defaults write com.apple.dock show-recents -bool false

# 关闭窗口最小化时的动画效果（缩放动画 → 直接消失）
defaults write com.apple.dock mineffect -string "scale"

# 关闭双击标题栏最大化窗口（改为无操作）
defaults write NSGlobalDomain AppleActionOnDoubleClick -string "None"

# 关闭应用打开时 Dock 图标弹跳动画
defaults write com.apple.dock launchanim -bool false

# 关闭自动隐藏 Dock 的延迟（如果你用自动隐藏的话，让它立刻出现）
defaults write com.apple.dock autohide-delay -float 0

# 关闭 Dock 自动隐藏的动画时间（瞬间出现/消失）
defaults write com.apple.dock autohide-time-modifier -float 0

# 关闭在 Dock 中显示建议的和最近的应用
defaults write com.apple.dock show-recent-count -int 0

# ============================================================
# 窗口行为相关
# ============================================================

# 关闭关闭窗口时的动画
defaults write NSGlobalDomain NSAutomaticWindowAnimationsEnabled -bool false

# 关闭打开/关闭应用时的动画
defaults write com.apple.finder DisableAllAnimations -bool true

# 关闭调整窗口大小时的动画
defaults write NSGlobalDomain NSWindowResizeTime -float 0.001

# 关闭 Mission Control 的动画速度（加快切换）
defaults write com.apple.dock expose-animation-duration -float 0.1

# ============================================================
# 其他烦人的东西
# ============================================================

# 关闭自然滚动方向（鼠标用户友好，触控板用户可能要保留）
# defaults write NSGlobalDomain com.apple.swipescrolldirection -bool false

# 关闭按键重复前的延迟（让按住键重复输入更快触发）
defaults write NSGlobalDomain InitialKeyRepeat -int 15

# 加快按键重复速度
defaults write NSGlobalDomain KeyRepeat -int 2

# ============================================================
# 重启相关服务使设置生效
# ============================================================

echo "重启 Dock..."
killall Dock

echo "重启 Finder..."
killall Finder

echo "重启 SystemUIServer..."
killall SystemUIServer

echo ""
echo "搞定。部分设置可能需要注销或重启才能完全生效。"
echo "如果苹果下次更新又给你全开回来，再跑一遍这个脚本。"
