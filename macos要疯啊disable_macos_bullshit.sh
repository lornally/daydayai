#!/bin/bash

# ============================================================
# macOS 反人类功能一键关闭脚本
# 作者：愤怒的用户 --kimi
# 用途：每次 macOS 更新后自动修正/窗口贴靠/Dock 设置被重置时，一键恢复
# 注意：执行后建议注销并重新登录，或重启电脑，以确保所有设置生效
# ============================================================

echo "正在关闭 macOS 反人类功能，请稍候..."

# ------------------------------------------------------------
# 第一部分：全局自动文本 / 键盘（最可恨的区域）
# 位置：系统设置 → 键盘 → 文本输入 → 编辑
# ------------------------------------------------------------

# 1. 自动拼写修正
# 作用：把 "iphone" 自动改成 "iPhone"，把中文人名瞎几乱改
# 副作用：写代码、写品牌名（如 bauhaus）、写中文名时会被强制修改
defaults write -g NSAutomaticSpellingCorrectionEnabled -bool false

# 2. 首字母自动大写
# 作用：每句话第一个字母强制变大写
# 副作用：写品牌名、文件路径、代码变量时会被强制修改
defaults write -g NSAutomaticCapitalizationEnabled -bool false

# 3. 智能引号
# 作用：把直引号 " " 改成弯引号 " "
# 副作用：写 Markdown、代码、命令行时引号会被改，导致格式错误或命令失效
defaults write -g NSAutomaticQuoteSubstitutionEnabled -bool false

# 4. 智能破折号
# 作用：把两个连字符 -- 改成 em dash —
# 副作用：写命令行参数（如 --help）时会被改掉
defaults write -g NSAutomaticDashSubstitutionEnabled -bool false

# 5. 自动句号（双击空格变句号）
# 作用：快速按两下空格自动插入句号
# 副作用：中文输入时空格本来就用得少，英文写代码时空格更是不能随便变句号
defaults write -g NSAutomaticPeriodSubstitutionEnabled -bool false

# 6. 自动文本替换
# 作用：系统级别的文本替换（如 (c) → ©）
# 副作用：可能会把正常输入的缩写或符号替换成你不想要的东西
defaults write -g NSAutomaticTextSubstitutionEnabled -bool false

# ------------------------------------------------------------
# 第二部分：窗口管理（macOS Sequoia 15+ 新增的反人类功能）
# 位置：系统设置 → 桌面与程序坞 → 窗口
# ------------------------------------------------------------

# 7. 拖动窗口到屏幕边缘自动贴靠（Window Tiling / 窗口贴靠）
# 作用：把窗口拖到屏幕边缘时，自动 resize 成半屏或四分之一屏
# 副作用：只想把窗口移开一点，结果突然被强制 resize，打断工作流
defaults write com.apple.WindowManager EnableTilingByEdgeDrag -bool false

# 8. 按住 Option 键拖动窗口到边缘也贴靠
# 作用：上面功能的 Option 键修饰版本
# 副作用：按住 Option 拖动本来是精确调整位置用的，结果也被劫持
defaults write com.apple.WindowManager EnableTilingOptionAccelerator -bool false

# 9. 拖动窗口到菜单栏/标题栏自动填充
# 作用：把窗口拖到屏幕顶部时，自动最大化或触发其他窗口操作
# 副作用：想把窗口往上移一点，结果突然被强制最大化
defaults write com.apple.WindowManager EnableTopshelf -bool false

# 旧版兼容（早期 Sequoia Beta 可能用的 domain，一并处理，无害）
defaults write com.apple.dock windowTilingByEdgeDrag -bool false 2>/dev/null

# ------------------------------------------------------------
# 第三部分：窗口标题栏行为
# 位置：系统设置 → 桌面与程序坞 → 窗口 → 点按窗口标题栏以
# ------------------------------------------------------------

# 10. 双击窗口标题栏的行为
# 可选值：
#   - "None"      : 什么都不做（推荐，最安静）
#   - "Minimize"  : 最小化窗口
#   - "Maximize"  : 缩放窗口（进入全屏或最大化）
# 副作用：如果不设为 None，双击标题栏时窗口会突然最小化或乱跳
defaults write NSGlobalDomain AppleActionOnDoubleClick -string "None"

# ------------------------------------------------------------
# 第四部分：程序坞（Dock）相关
# 位置：系统设置 → 桌面与程序坞
# ------------------------------------------------------------

# 11. 不显示最近使用的应用程序
# 作用：Dock 右侧不会显示你最近打开过的应用图标
# 副作用：无，通常用户自己知道要去哪里找应用
defaults write com.apple.dock show-recents -bool false

# 12. 最小化窗口时缩略图合并到应用程序图标
# 作用：true = 最小化后窗口缩略图不单独占 Dock 位置，而是合并到对应应用图标上
#       false = 最小化后窗口缩略图出现在 Dock 右侧，占一堆位置
# 副作用：设为 true 可以让 Dock 右侧干净一些；如果你之前被一堆缩略图烦到，保持 true
defaults write com.apple.dock minimize-to-application -bool true

# 13. 关闭最小化动画（可选，如果你嫌 Dock 最小化动画慢）
# defaults write com.apple.dock launchanim -bool false

# 14. 关闭打开应用时的弹跳动画（可选）
# defaults write com.apple.dock launchanim -bool false

# ------------------------------------------------------------
# 第五部分：Finder 反人类功能
# 位置：Finder → 设置 → 高级
# ------------------------------------------------------------

# 15. 显示所有文件扩展名
# 作用：防止 macOS 隐藏文件后缀，避免 "document" 实际上是 "document.txt" 但你不知道
defaults write NSGlobalDomain AppleShowAllExtensions -bool true

# 16. 禁止在 USB/网络盘创建 .DS_Store 文件
# 作用：.DS_Store 是 macOS 用来存文件夹视图设置的隐藏文件，会污染 U 盘、共享文件夹
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true

# ------------------------------------------------------------
# 第六部分：中文输入法（无法直接用 defaults 彻底关闭，需手动）
# ------------------------------------------------------------

echo ""
echo "【注意】中文输入法的自动修正设置无法通过命令行关闭，请手动检查："
echo "    系统设置 → 键盘 → 文字输入 → 简体中文-拼音 → 编辑"
echo "    关闭：自动纠正拼写、智能引号、智能破折号"
echo ""

# ------------------------------------------------------------
# 重启相关服务使设置生效
# ------------------------------------------------------------

echo "正在重启 Dock 和 Finder..."
killall Dock
killall Finder

echo ""
echo "========================================"
echo "设置已完成！"
echo "========================================"
echo ""
echo "以下设置已关闭："
echo "  ✗ 自动拼写修正"
echo "  ✗ 首字母大写"
echo "  ✗ 智能引号 / 智能破折号"
echo "  ✗ 双击空格变句号"
echo "  ✗ 自动文本替换"
echo "  ✗ 窗口边缘贴靠"
echo "  ✗ 窗口标题栏拖动触发"
echo "  ✗ Option 键窗口贴靠"
echo "  ✗ 双击标题栏最小化/最大化"
echo "  ✗ Dock 最近使用应用"
echo ""
echo "建议操作："
echo "  1. 注销并重新登录（最保险）"
echo "  2. 或重启电脑"
echo "  3. 然后打开‘系统设置’手动检查一遍，确认勾都关掉了"
echo ""
echo "如果未来 macOS 更新后这些设置又回来了，重新运行本脚本即可。"
echo "========================================"
