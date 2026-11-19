# wescom 显示器"不亮" — 诊断与修复参考文档

> 首次处理: 2026-11-19
> 现场机器: Mac Studio (M1 Max, `Mac13,1`), macOS 15 (Darwin 24.6)
> 另一台: macOS 26 的 Mac，同样出现 wescom 不亮（其细节未在本机验证）
> 显示器: wescom `W2876ZZY`（4K 60Hz，走 USB-C / DP Alt Mode）; 正常屏 `L32J1`（4K 75Hz，主屏）

## 0. 结论先行

- **问题在 wescom 显示器自身的固件**：它在系统进入显示器待机（DPMS off）后再唤醒时，DisplayPort 链路握手会卡死 —— 面板不亮、屏幕上的 OSD 菜单按键也无响应。
- **不是 macOS 的问题**：同型号屏在两台不同 Mac（macOS 15 与 macOS 26）上都复现；同一台 Mac 上另一块屏（L32J1）从不复现。macOS 侧始终认为该显示器 `Online`，一直在输出 4K60 信号。
- **不需要重启 Mac**：通过软件强制显示器链路重新协商（切换刷新率再切回）即可唤醒，约 3 秒。脚本已自动化：`fix-wescom`（手动）和看护服务（自动）。
- 本目录提供一次性安装：`./install.sh`。装完之后正常休眠不受影响，唤醒后若检测到卡死会自动修复。

## 1. 现象

1. 正常使用中，显示器休眠（或睡眠唤醒）之后，wescom 这块屏不亮。
2. 此时按显示器自身的 OSD 菜单键，**菜单也弹不出来**（说明显示器主控卡死，不是简单无信号）。
3. 重启 Mac 可以恢复 —— 所以用户一直以为只能重启。
4. 另一台 Mac（macOS 26）上的 wescom 也经常不亮；标准配置的另一块屏从不出现。
5. 两台机器各自独立连接，不存在共用线材。

## 2. 现场证据（关键）

在 Mac 端执行：

```bash
system_profiler SPDisplaysDataType
```

即使 wescom 面板是黑的，系统仍报告：

```
W2876ZZY:
  Resolution: 3840 x 2160 (2160p/4K UHD 1)
  UI Looks like: 1920 x 1080 @ 60.00Hz
  Online: Yes          <-- 关键：Mac 认为它在线
```

链路拓扑（`ioreg`）：

```bash
ioreg -t -l -w0 -r -c AppleCLCD2
```

- `dispext0` → `L32J1`（厂商 ID `XSL`，Serial 6666，75Hz，PortID 48）
- `dispext1` → `W2876ZZY`（厂商 ID `WSM`，ProductID 9984，Serial **1**，60Hz，PortID 0）
- W2876ZZY 的 EDID 是公版模板：`AlphanumericSerialNumber = "0000000000001"`、`WeekOfManufacture = 33`、`YearOfManufacture = 2025` —— 廉价屏通用方案，固件粗糙。
- `DisplayAttributes` 显示 `SupportsSuspend=No`, `SupportsStandby=Yes` —— macOS 会走 DPMS standby 路径。

结论：**信号链路是通的（EDID 能读、系统认为在线），黑屏发生在这之后的显示器侧**。

## 3. 判断流程（换一台机器也按这个来）

```
显示器黑了
│
├─ 在 Mac 上跑 system_profiler SPDisplaysDataType
│   │
│   ├─ 黑屏仍显示 Online + 分辨率/刷新率
│   │     => Mac 在输出信号, 问题在显示器 (待机唤醒/面板/输入源)
│   │     => 先做本文的链路重协商 (fix-wescom); 不行再查显示器
│   │
│   └─ 列表里没有这块屏 / 显示 Offline
│         => 链路问题: 线材、接口、转接器/扩展坞、显示器电源
│         => 换线、换口 (USB-C <-> HDMI)、绕开转接器、查显示器电源
│
├─ 同一块屏在多台 Mac 上复发 + 其他屏都正常
│     => 显示器型号/固件通病 (本例)
│
└─ 只有某一台 Mac 出问题, 换台机器正常
      => 那台 Mac 的口/线/转接器问题
```

注意反面案例：不要假设"两台机器共用一根线" —— 本例是两台独立机器各自的屏，共同变量是 **wescom 这个型号**。

## 4. 根因分析

- macOS 让显示器休眠用的是 DPMS standby；唤醒时需要重新做 DisplayPort link training。
- wescom 固件在 `standby -> on` 的握手上卡死：AUX/DDC 不再应答、面板与 OSD 全无响应，但 macOS 侧链路对象仍在（EDID/Online 状态保持），所以系统看起来一切正常。
- 重启 Mac 之所以"有效"：整条 DCP/链路被重建，相当于替显示器重做了一次握手。与 macOS 本身无关。
- 显示器休眠期间的实际状态没有采集到（测试时屏幕被用户操作立即唤醒）；因此自动检测不使用"睡眠状态推断"，而是用系统日志做门控（见下）。

## 5. 修复原理

用 CoreGraphics 强制改变显示模式：

1. 把**所有外接屏**的刷新率切到另一个支持的值（如 60→30Hz；75→50Hz）；
2. 等 3 秒；
3. 切回原值。

模式切换会触发 DCP/GPU 侧重新 mode set，DisplayPort 重新协商/训练，效果等同于重启 Mac 对显示链路的作用，但只影响几秒钟，窗口与应用不受影响。

验证记录（2026-11-19）：

- 卡死时 DDC 读亮度 = `0`；执行上述切换后屏幕点亮。
- 亮屏后 DDC 读亮度 = `49`（Contrast `50`）；主屏 L32J1 读亮度 = `80`。
- 因此可用 **DDC 亮度读数**区分"卡死(0)"与"正常(>0)"。

## 6. 自动检测与看护设计

`wescom-watchdog`（由 launchd 常驻）：

1. 每 10 秒用 `pmset -g log | grep 'Display is turned (on|off)' | tail -1` 判断当前屏幕状态；
2. 只在 **off → on 的转换之后**开启一个 60 秒检查窗口（正常休眠/关屏期间绝不动作）；
3. 窗口内通过 DDC 读 wescom 亮度：
   - 读不到（空）→ DDC 不可用，不自动动手，留手动 `fix-wescom`；
   - 读到 >0 → 正常，清零计数；
   - 读到 0 连续两次（约 20 秒）→ 判定卡死，执行 `fix-wescom` 重新协商，然后本窗口内不再重复动作。
4. 开机/登录时（RunAtLoad）也会有一个 45 秒初始检查窗口，覆盖"开机就黑"的场景。

为什么不用 caffeinate 常亮：用户明确不接受屏幕 24 小时常亮（晚上要关屏）。看护方案允许正常休眠，只在醒来可能卡死时兜底。

DDC 工具：
- Apple Silicon：`m1ddc`（`m1ddc display list` / `m1ddc display N get luminance`）。
- Intel：`ddcctl`（`ddcctl -d N -b` 读取，语法需按版本验证；若读不可靠，自动修复会自然跳过，只保留手动方案）。

其他实测备注：
- `pmset -g powerstate IODisplayWrangler` 和 `ioreg -n IODisplayWrangler` 在本机取不到有效的显示器电源状态（返回空/Internal failure），所以改用 `pmset -g log` 的事件判断。
- `pmset displaysleepnow` 可以在非 root 下执行，但若系统开了"关闭显示器后需要密码"，会导致锁屏（本机测试时触发过一次）——文档读者注意别在工作时间随意调用。

## 7. 本目录文件与使用

| 文件 | 用途 |
|---|---|
| `README.md` | 本文档 |
| `install.sh` | **每台机器执行一次**：装依赖 + 安装脚本 + 加载看护服务 |
| `fix-wescom` | 手动修复命令（自动探测屏幕，跨机器通用）；`-n` 只打印不执行 |
| `wescom-watchdog` | 看护循环（由 install.sh 安装为 launchd 服务，无需手动跑） |

安装（每台机器一次）：

```bash
cd "这个目录"
./install.sh
```

完成后的效果：

- 正常休眠照旧（不常亮）；
- 屏幕醒来后约 10~20 秒内，若 wescom 卡死会被自动修复；
- 任何时候也可以手动 `fix-wescom`（约 3 秒，两屏各闪一下，属正常）。

日志：`/tmp/wescom-watchdog.log`

卸载：

```bash
launchctl bootout gui/$(id -u)/com.user.wescom-watchdog
rm ~/Library/LaunchAgents/com.user.wescom-watchdog.plist \
   ~/.local/bin/fix-wescom ~/.local/bin/wescom-watchdog
```

## 8. 迁移到其他 Mac（含 Intel + macOS 12）

依赖与兼容性：

- `displayplacer`（Homebrew，v1.4.0 实测）：基于 CoreGraphics，Intel / Apple Silicon 均可用；macOS 12 可运行。脚本每台机器自动探测屏幕 ID 与可用模式，**无需改代码**。
- `m1ddc`：Apple Silicon（M 系）专用；`ddcctl`：Intel 专用。`install.sh` 会按 `uname -m` 自动选择。
- 国内网络注意：`brew install` 需要代理（ghcr.io / GitHub）。

迁移步骤：

1. 把整个目录拷到新机器（AirDrop / U 盘 / 网盘均可）；
2. `./install.sh`；
3. 完事。多屏布局、分辨率、主副屏关系都不影响（脚本按当前实际配置生成命令）。

Intel + macOS 12 的已知注意事项（未在实机验证，下一个 AI 请按此验证/修正）：

- `displayplacer` 应正常；若 Homebrew 版本不提供 arm 编译包以外的支持，`brew install displayplacer` 会自动取 x86_64 bottle。
- `ddcctl` 的**读取**语法与输出格式随版本略有差异，先手动验证：
  - 显示器正常时：`ddcctl -d 2 -b` 能读到亮度数值；
  - 卡死时：同样命令应返回 0 或失败。
  - 若输出无法稳定解析，`wescom-watchdog` 会自动跳过自动修复（不会乱动），此时手动 `fix-wescom` 仍可用。
- macOS 12 上 `pmset -g log` 的 "Display is turned on/off" 事件格式需确认；若不一致，替换看护脚本中的判断（`last=$(...)` 那段）即可。
- Intel + 外接 AMD GPU 等组合，mode set 依然会触发链路重协商，原理不变。
- 如果目标显示器走 HDMI 而不是 USB-C/DP：模式切换原理同样适用（HDMI 也有链路训练）。

## 9. 如果这个修复不起作用 — 排查清单

按顺序尝试：

1. **显示器拔电源 10 秒**再插回（最原始、最有效；能恢复说明就是待机卡死）。
2. 拔插视频线；换线；换接口（USB-C ↔ HDMI）；绕开扩展坞/转接器。
3. 在屏幕正常点亮时，进显示器 OSD 设置：
   - DP 版本改为 1.2（不要 1.4）；
   - 关闭 Deep Sleep / 深度睡眠 / ECO；
   - 输入源固定为实际使用口（关闭自动检测）。
4. 系统侧软复位：`pmset displaysleepnow` 后唤醒（注意可能锁屏），相当于完整 DPMS 循环。
5. 极端手段：`sudo killall WindowServer`（会注销图形会话，程序会退出，慎用）。
6. 以上都无效 → 显示器固件无解，考虑保修/换屏（本例根因在固件，Mac 侧只能绕过）。
7. 给后续 AI/维修人员采集证据：
   - `system_profiler SPDisplaysDataType`：黑屏时是否 Online；
   - `ioreg -t -l -w0 -r -c AppleCLCD2`：EDID、厂商 ID、端口；
   - DDC 亮度读数（正常 vs 卡死）；
   - `pmset -g log | grep 'Display is turned'`：休眠/唤醒时间线。

## 10. 关键命令速查

```bash
# 显示器/链路状态
system_profiler SPDisplaysDataType
ioreg -t -l -w0 -r -c AppleCLCD2 | grep -iE 'DisplayAttributes|ProductName|Transport'

# DDC 探测 (Apple Silicon)
m1ddc display list
m1ddc display 2 get luminance        # 正常 >0; 卡死 = 0

# 显示模式配置 (displayplacer)
displayplacer list                   # 每个屏的 Persistent screen id / 当前模式 / 支持的模式
displayplacer "id:<ID> res:... hz:... color_depth:8 scaling:on origin:... degree:0"

# 屏幕电源事件时间线
pmset -g log | grep -E 'Display is turned (on|off)' | tail

# 本方案的修复
fix-wescom
```

## 11. 变更记录

- 2026-11-19：首次诊断与修复。确认 wescom 固件待机唤醒卡死；以 displayplacer 刷新率切换恢复；安装 DDC 看护服务；产出本目录脚本与文档。
