# macOS 终端启动慢排查与优化

## 症状

- VSCode 提示"无法在合理的时间内解析配置"
- 新开终端窗口卡顿数秒
- 关闭窗口时显示有 `bash, sleep` 进程在运行

## 排查方法

```bash
# 测量 shell 启动时间
time zsh -i -c exit

# 多次测量取平均（random theme 会有波动）
for i in 1 2 3 4 5; do time zsh -i -c exit 2>&1 | grep total; done

# macOS Terminal 每个窗口都是 login shell，加载顺序：
# .zprofile → .zshrc → .zlogin
```

## 常见拖慢原因及修复

### 1. nvm 初始化（最常见，耗时 0.5-1s）

问题写法：
```bash
export NVM_DIR="$HOME/.nvm"
source "$(brew --prefix nvm)/nvm.sh"  # brew --prefix 本身就慢
```

修复方案 A - 懒加载（推荐，需要用 node 时）：
```bash
export NVM_DIR="$HOME/.nvm"
nvm() {
  unset -f nvm node npm npx
  [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && source "/opt/homebrew/opt/nvm/nvm.sh"
  nvm "$@"
}
node() { unset -f nvm node npm npx; [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && source "/opt/homebrew/opt/nvm/nvm.sh"; node "$@"; }
npm() { unset -f nvm node npm npx; [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && source "/opt/homebrew/opt/nvm/nvm.sh"; npm "$@"; }
npx() { unset -f nvm node npm npx; [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && source "/opt/homebrew/opt/nvm/nvm.sh"; npx "$@"; }
```

修复方案 B - 直接注释（不用 node 时）：
```bash
#export NVM_DIR="$HOME/.nvm"
#[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && source "/opt/homebrew/opt/nvm/nvm.sh"
```

### 2. .zprofile 中的阻塞脚本

问题：SSH 预连接脚本在前台执行，内部 sleep 循环等待代理最多 15 秒：
```bash
~/.ssh/ensure-github-connection.sh 2>/dev/null  # 阻塞！
```

修复：直接注释掉。SSH ControlMaster 会在首次 git 操作时自动建立持久连接。
```bash
# ~/.ssh/ensure-github-connection.sh 2>/dev/null
```

### 3. oh-my-zsh random theme

`ZSH_THEME="random"` 每次随机主题，某些重主题会偶发变慢。
固定轻量主题可消除波动：
```bash
ZSH_THEME="robbyrussell"  # 默认主题，极轻
```

### 4. $(brew --prefix ...) 动态查询

任何 `$(brew --prefix xxx)` 都会调用 brew 查数据库，耗时 200-500ms。
改成硬编码：
```bash
# 慢
source "$(brew --prefix nvm)/nvm.sh"

# 快（先用 brew --prefix nvm 查一次，把结果写死）
source "/opt/homebrew/opt/nvm/nvm.sh"
```

## 优化效果

| 阶段 | 启动时间 |
|------|----------|
| 优化前（nvm + SSH 脚本阻塞） | 3-15 秒 |
| 注释掉 nvm + SSH 脚本 | ~0.12 秒 |

## 快速检查清单

- [ ] `.zprofile` 里有没有阻塞命令（网络请求、sleep、等待进程）
- [ ] `.zshrc` 里 nvm/rvm/conda 是否可以懒加载或注释
- [ ] oh-my-zsh plugins 是否精简（`plugins=(git z)` 够用）
- [ ] 有没有 `$(brew --prefix ...)` 动态查询，改成硬编码路径
- [ ] pnpm/yarn 等 PATH 配置如果不用也注释掉
