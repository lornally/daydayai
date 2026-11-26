# wescom 显示器"不亮" — 诊断与修复参考文档

> 首次处理: 2026-11-19
> 机器 1: Mac Studio (M1 Max, `Mac13,1`), macOS 15 (Darwin 24.6)
> 显示器: wescom `W2876ZZY`（4K 60Hz，走 USB-C / DP Alt Mode）; 正常屏 `L32J1`（4K 75Hz，主屏）
> 机器 2: Mac Studio (M1 Max, `Mac13,1`), macOS 27.2.1 (Darwin 27.2.0)，2026-11-23 处理
> 显示器: WSM `C3273IUY`（4K 60Hz，USB-C 4 口）; 正常屏 `PHL 438P1`、`MSI PS341WU`

## 0. 结论先行

- **问题在 wescom 显示器自身的固件**：它在系统进入显示器待机（DPMS off）后再唤醒时，DisplayPort 链路握手会卡死 —— 面板不亮、屏幕上的 OSD 菜单按键也无响应。
- **不是 macOS 的问题**：同型号屏在两台不同 Mac（macOS 15 与 macOS 26）上都复现；同一台 Mac 上另一块屏（L32J1）从不复现。macOS 侧始终认为该显示器 `Online`，一直在输出 4K60 信号。
- **不需要重启 Mac**：通过软件强制显示器链路重新协商（切换刷新率再切回）即可唤醒，约 3 秒。脚本已自动化：`fix-wescom`（手动）和看护服务（自动）。
- **2026-11-24 更新**：被 macOS 移出桌面的显示器还可以用 SkyLight 私有接口**软件接回**，不需要拔线；
  详见 §12.7。物理拔插从“唯一手段”降为“最后的兜底”。
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
| `install.sh` | **每台机器执行一次**：装依赖 + 安装脚本/编译工具 + 加载看护服务 |
| `fix-wescom` | 手动修复命令（自动探测屏幕，跨机器通用）；`-n` 只打印不执行 |
| `wescom-dpfix.c` | 软件重连工具源码，编译为 `~/.local/bin/wescom-dpfix`；`list/find/on/off/replug` |
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
- 2026-11-23：第二台 Mac Studio（macOS 27.2.1）上复现并处理。新增 WSM 厂商识别、DDC 电源唤醒、同分辨率重协商、物理恢复提示；详见 §12。

## 12. 2026-11-23 补充：macOS 27 Mac Studio（WSM `C3273IUY`）

### 12.1 这台机器的情况

- Mac Studio (M1 Max, `Mac13,1`)，macOS 27.2.1 (Darwin 27.2.0)。
- 三块屏：`C3273IUY`（厂商 **WSM**，4K，USB-C 4 口，主屏）、`PHL 438P1`（Philips，走 DP→HDMI 转接）、`MSI PS341WU`（5K2K 带鱼屏，DP）。
- WSM 屏和老 wescom 是同一厂商（`ManufacturerID=WSM`），EDID 同样是公版模板（`AlphanumericSerialNumber=0000000000001`，`SerialNumber=0`，`SupportsStandby=Yes`）。
- 症状与老机器一致：屏幕黑、OSD 无响应，但 macOS 仍报告 `Online` 和分辨率。也是休眠唤醒后触发。

### 12.2 和老机器不同的关键点（后续 AI 必读）

1. **卡死时 DDC 直接失效**：老机器卡死时 DDC 仍能读，亮度为 `0`；这台机器卡死时 `m1ddc get luminance/contrast/volume/input` 全部报
   `DDC communication failure: (iokit/?) unknown subsystem error`。健康时 DDC 完全正常（亮度 50、对比度 50、`standby=1`、`input=7`）。
   → **检测判据**：DDC 读数 `0` 或通信失败，都算卡死；连续 3 次才动作，避免误判。
2. **大跨度模式切换会把屏从链路里踢掉**：在卡死状态下把 WSM 切到 `3840x2160@50Hz`，屏幕没有被唤醒，反而从 CoreGraphics/IOKit 里消失
   （`system_profiler`、`displayplacer`、`m1ddc` 都只剩两块屏）。此时**只关显示器电源、再开，Mac 仍不会重新注册这块屏**；
   当时只有把 **USB-C 视频线从 Mac 端拔下再插回**（热插拔），macOS 才会重新接纳。
   → **禁止**把任意大分辨率/刷新率切换作为自动恢复动作。

   > 2026-11-24 更正：后来找到 SkyLight 软件重连接口，被移出桌面的屏可以**不拔线**接回（§12.7）。
   > “必须拔线”是当时还不知道这个接口时的结论。物理拔插现在只是最后兜底。
3. **这块屏没有“同分辨率换刷新率”的备选**：displayplacer 在 `1920x1080` 下列了 3 个条目，实际只有 2 种配置——
   HiDPI on（本质是 4K 模式 `3840x2160` + WindowServer `Scale=2`）和 1x（CoreGraphics 里有两个重复条目 modeID 23/65，均 1920x1080@60）。
   两种配置全部 60Hz；50Hz 只出现在 `1280x720`、`3840x2160 scaling:on`、`640x360`、`720x576`；没有任何 30Hz。
   注意这是 **macOS/EDID 暴露的模式表**，不代表面板硬件做不到 1080p50；加自定义 timing 需要 BetterDisplay/SwitchResX 之类工具，不在本方案内。
   因此老机器“只调频率”的方案在这块屏上不可用。曾实测把 HiDPI 切成 1x（`scaling:off`，同分辨率同刷新率）再切回：
   三屏全程在线、DDC 正常、窗口布局不变（只短暂变糊），但这是**改 backing 分辨率**，不是调频率，而且只验证了
   “健康时安全”，卡死时能否救活未验证。**默认不做**；只有手动 `fix-wescom -s` 才允许。
4. **DDC 写入可用**：`m1ddc 1.3.3` 支持 `set standby <1-4>`（VCP 0xD6），健康时 `set standby 1` 返回 `Writing 1`。
   脚本先尝试 DDC 电源唤醒，不闪屏，是最保守的一步。
5. **DDC 调用可能永久挂起**：实测 `m1ddc get mute` 一次挂了 120 秒以上。脚本里所有 DDC 读写都套了 5 秒超时
   （`perl -e 'alarm 5; exec @ARGV'`），避免看护服务卡死。

### 12.3 新脚本的恢复顺序

`fix-wescom` 与看护服务按以下顺序动作：

0. 屏被 macOS 移出显示列表 → 用私有 SkyLight 接口**软件重新接入**（`wescom-dpfix on`）。
1. 读 DDC 亮度；>0 直接退出（不动屏幕）。
2. `set standby 1` 尝试 DDC 电源唤醒。
3. **软件拔插**（`wescom-dpfix replug`：off → 2 秒 → on），重建显示管线。
4. 同分辨率换刷新率（**只调频率**；仅当 EDID 提供另一个刷新率。C3273IUY 没有 50/30Hz，所以这一步自动跳过）。
5. HiDPI ↔ 1x 切换（看护服务带 `-s` 调用；会改 backing 分辨率）。
6. 仍失败 → 输出物理恢复步骤，并（看护服务）发桌面通知。

每次动手前会把当前完整三屏配置保存到 `~/.local/state/wescom-last-config`，恢复后自动
`fix-wescom --restore` 恢复原 HiDPI/布局。看护服务在屏幕健康时也会刷新这份配置。

注：手动 `fix-wescom` 默认不带 `-s`（只调频率）；看护服务在频率方案不可用时带 `-s` 作为最后一步。

因此这台机器的日常恢复顺序是：**先等自动处理（软件接回/软件拔插 → DDC 唤醒 → 重协商）；不行才拔插 USB-C 线**。

### 12.4 建议的显示器 OSD 设置（从根上避免）

屏幕点亮时进入 OSD：

- 关闭 **Deep Sleep / 深度睡眠 / ECO / 自动待机**（中文可能叫“深度睡眠 / 休眠 / 省电模式 / 节能 / 无信号自动关机”）；
- **DP 版本设为 1.2**（不要 1.4；中文“DP 版本 / DisplayPort 版本”）；
- 打开 **DDC/CI**（如果默认关闭；中文可能叫“DDC/CI / DDC / 显示器控制 / PC 控制”，没有这一项就不用管）；
- 输入源固定为实际使用的 USB-C 口（关闭自动检测；中文“信号源 / 输入 / 自动选择”）。

注意：**Adaptive Sync / 自适应同步**是可变刷新率（FreeSync），不是 DDC/CI，与本问题无关，保持关闭/默认即可。

如果 OSD 没有这些选项，或改完仍复发：优先尝试换用 **HDMI** 连接（Mac Studio 自带 HDMI 口），
其次换一个 USB-C 口，最后考虑换屏。固件问题无法在 Mac 侧根治。

### 12.5 实测命令速查（macOS 27）

```bash
m1ddc display list detailed                 # 看 Manufacturer: WSM 和 IO Location
m1ddc display 1 get luminance               # 健康 50; 卡死: 通信失败/0
m1ddc display 1 set standby 1               # DDC 电源唤醒
displayplacer list                           # 看当前模式/备选模式
ioreg -lw0 | grep -A8 'SinkDeviceID'         # 看 DCP 链路是否 Active/Ready

wescom-dpfix list                            # CG 能看到的所有显示 (含 online=0)
wescom-dpfix find                            # 只列 WSM 厂商的屏
wescom-dpfix on 3                            # 软件接回 (不拔线)
wescom-dpfix off 3                           # 软件移出 / 模拟拔线
wescom-dpfix replug 3                        # off -> 2s -> on (软件拔插)
fix-wescom --save                            # 保存当前三屏布局
fix-wescom --restore                         # 恢复保存的布局/HiDPI
```

判断"屏是否被 macOS 移除"：`displayplacer list` / `m1ddc display list` 里没有 WSM 的 UUID（或 `system_profiler` 里没有该型号）——
先运行 `wescom-dpfix find`；能列出 `online=0` 就 `wescom-dpfix on <id>` 软件接回；连 CG 都看不到时才需要物理拔插。

### 12.6 为什么 macOS 会把这块屏“踢掉”？为什么以前以为必须拔插线？

不是灵异事件，分两段：

1. **显示器先卡死**：DPMS 唤醒时 wescom/WSM 固件没有完成链路握手，面板黑、OSD 无响应、DDC 也失效。
   此时 Mac 侧仍保留 EDID 和链路对象，所以 `system_profiler` 还显示 Online。
2. **Mac 侧的训练失败状态机**：切模式会让 DCP 重新做 DisplayPort link training。显示器无法完成训练，
   DCP 重试后放弃，把 sink 从 WindowServer 的活动显示集合移除（于是 `displayplacer`/`m1ddc` 里消失），
   但 DCP 的 `ConnectionMapping` 里仍留着 EDID（`SinkDeviceID`、`Active=Yes` 可能还在）。
   macOS 之后不会主动重新探测这个口；显示器断电重开不一定产生 WindowServer 能识别的 HPD 变化，
   所以仍然不回来。拔插 USB-C 线强制一次 HPD，WindowServer 才重新创建显示对象。
   （§12.7 更正：不需要等 HPD，WindowServer 也可以用 SkyLight 软件配置把屏接回。）

责任划分：

- 根因在显示器固件：同型号在两台 Mac（macOS 15 / macOS 26~27）复现；同机其他两块屏从不复现；卡死时显示器 OSD 也无响应。
- macOS 侧确实有“link training 失败后放弃、不自动重试”的次要问题，但**不是没有手动办法**：
  WindowServer 可以用 SkyLight 私有接口把屏接回（§12.7），不必等 HPD。物理拔插只是最后兜底。
  所以“只能拔线”这个中间结论是不完整的。

复现概率：`pmset displaysleepnow` + 唤醒是同一触发条件，但不保证每次都卡死。2026-11-24 06:53 的自然唤醒就正常
（看护日志没有异常读数），说明是间歇性问题。只能等自然复发时收集数据；看护服务会自动记录 DDC 读数、
重协商结果和通知时间线。

### 12.7 2026-11-24：软件层重新接入成功（推翻“只能拔线”）

**结论**：只要 macOS 的 DCP 还认这块屏（`ioreg` 里 `SinkDeviceID`/`Active` 还在），
WindowServer 即使把它移出桌面，也可以用私有 SkyLight 接口把它接回来，不需要物理拔插。

关键私有符号（macOS 27.2.1 实测存在，dlopen 自
`/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight`）：

- `SLSConfigureDisplayIndependentOutput(cfg, displayID, bool)`
- `SLSConfigureDisplayEnabled(cfg, displayID, bool)`

配合公开的 `CGBeginDisplayConfiguration` / `CGCompleteDisplayConfiguration(cfg, .forSession)`
（2026-11-26 起由 `.permanently` 改为 session 级：`off` 之后若进程被打断，缺屏状态不会写进永久配置）：

- 接回：`IndependentOutput=false` + `Enabled=true`
- 移出：`IndependentOutput=true`
- 软件拔插：先移出、等 2 秒、再接回

开源项目 [DisplayLatch](https://github.com/Hitesh-Sisara/DisplayLatch)（MIT）用了同样的接口；
本目录的 `wescom-dpfix.c` 是精简实现，`install.sh` 自动编译。

实测记录（2026-11-24，macOS 27.2.1）：

- `PHL 438P1`：`off` → `online=0` → `on` → `online=1`，全程不拔线。
- `WSM C3273IUY`（主屏）：同样 `off/on` 成功，主屏身份恢复；`fix-wescom --restore` 恢复左右屏排列。
- 端到端：`wescom-dpfix off 3` 模拟 macOS 把 WSM 移出桌面 → `fix-wescom` 自动执行
  `wescom-dpfix on 3` → DDC 读到 50 → 三屏原布局/HiDPI/主屏全部恢复，退出码 0。
- 期间还发现并修复了一个误判 bug：旧 `resolve_idx` 在找不到 WSM 时会拿“最后一块屏”兜底，
  多屏机器上会把 PHL 的亮度当成 WSM 的；现已移除该兜底。

注意：

- 这套接口解决的是“macOS 把屏移出桌面/禁用”的问题。如果显示器固件把 DP 链路也彻底弄死
  （DCP 不再认这块屏），软件接回也无效，仍需物理拔插/换口。当前 WSM 卡死时 DCP 链路仍然是 Active，
  所以很可能软件拔插就能解决——等下一次自然复发时看护日志会给出结论。
- Intel + macOS 12：SkyLight 符号是否存在未验证；`wescom-dpfix` 启动时会检查，缺失则退出码 10，
  `fix-wescom` 自动回退到 DDC/刷新率/物理拔插方案。
- 私有 API 未来可能变动；工具在运行时 dlopen/dlsym，符号缺失只降级不崩溃。
- 2026-11-26 在 macOS 15.8.3 补测：符号正常、`find` 能认出 WSM；
  `off 2` → `online=0` → `on 2` → `online=1` 全程不拔线，布局和 DDC 亮度(49)都保持。

## 13. 2026-11-26 更新（macOS 15 机器，第二次升级后）

### 13.1 现象与结论：新脚本自己变慢了

用户反馈“换新脚本后好几次过好久显示器才亮”。看护日志实测：14:10:37 唤醒 → 14:12:19 才恢复，约 **102 秒**；
11.19 老脚本约 25~40 秒。根因是脚本时序/顺序，不是显示器变差：

1. **检测慢**：亮屏后先等 15 秒，再要连续 3 次坏读数；每次 `m1ddc display list` 没加超时，卡死时单次会挂 20 秒+，
   实际约 70 秒才开始修。
2. **修复顺序不对**：先 DDC 电源唤醒、再软件拔插，最后才做老机器反复验证有效的“换刷新率”。
   14:11 的日志证明前两步都没救活，真正起效的是最后一步，白等约 20 秒。
3. **`--save` 会用残缺配置覆盖完整配置**（18:07 保存的只剩 WSM 一块屏），之后 `--restore` 反而会把多出来的屏踢掉。

### 13.2 当天另一个发现：另一块屏（sanguang / L32J1，厂商 XSL）掉链路

- WindowServer 日志：17:14:58 hotplug **in**（display id 4），17:14:59 又 hotplug **out** ——
  显示器自己在唤醒 1.7 秒后把 DP 链路掉了，之后一直没回来。
- 这是“链路真的断了”，不是 macOS 把屏移出桌面：`displayplacer`、`m1ddc`、`system_profiler` 完全看不到它，
  `ioreg` 里 dispext0 的 AppleCLCD2 连 EDID 都没有；`wescom-dpfix on 4` 返回 5
  （`CGCompleteDisplayConfiguration` 失败）。软件无解，只能拔电源线等 15 秒再插回（详见 §13.6）。
- 区分方法：`wescom-dpfix list` 里 `online=0` 且 `on` 失败 = 链路断了；
  `online=0` 且 `on` 成功 = macOS 桌面层问题（软件可救）。

### 13.3 本次改动

- `wescom-watchdog`：亮屏后 **5 秒**开始、**每 3 秒**一轮、窗口 90 秒；连续 3 次坏读数即修复。
  同时扫描所有 CG 里 `online=0` 的其它屏：先软件接回，接不回立刻桌面通知（提示断电重开）。
- `fix-wescom`：恢复顺序改为 **换刷新率（仅 hz 备选）→ DDC 唤醒 → 软件拔插 → 缩放（仅 -s）**。
  所有 `m1ddc` 列表调用加 5 秒超时；DDC 完全无响应（读数为空）时跳过 DDC 唤醒，少等约 10 秒。
- `--save` / `--restore` 防残缺配置：当前屏数少于已保存屏数时拒绝覆盖/恢复。
- 新增 `scan_other_displays`：手动跑 `fix-wescom` 也会顺手处理其它 offline 屏（WSM 主流程不变）。

### 13.4 验证

- `fix-wescom -n` 应输出 WSM 状态 + 不在线屏的提示（本机实测：识别出 sanguang 不在线）。
- 看护日志新格式：`display on -> checking in 5s`、`offline display 4 ... link down`。
- 下次 WSM 卡死时，日志应看到先做“模式重协商”，且整个恢复在 30~40 秒内完成。

### 13.5 “macOS 不能直接触发重新检测吗？”——能，但对本机的 sanguang 无效

macOS 内部确实有“重新检测显示器”的实现，2026-11-26 已在本机确认并反汇编：

- `SLSDetectDisplays()`（SkyLight / DisplayServices 私有符号，无参数）就是老的“Detect Displays”实现：
  它列出系统显示列表，对每块屏用 `SLSServiceForDisplayNumber(id, &svc)` 拿到 IO 服务，
  再对服务发 `IOServiceRequestProbe(svc, 1)`。
- 但这套只能探测“系统里还有 IO 服务”的屏。对已经掉链路的 sanguang（XSL，cgid 4）实测：
  - `SLSServiceForDisplayNumber(4)` 返回 0 但 `svc = 0` —— 没有可探测对象；
  - 直接对 `dispext0` 的 AppleCLCD2 / dcpdptx-port 服务发 `IOServiceRequestProbe` → `0xE00002C7`（kIOReturnUnsupported）；
  - `ioreg` 里 dispext0 的 AppleCLCD2 没有任何 EDID/DisplayAttributes（WSM 的节点有）。
- 结论：`online=0` 且 `SLSServiceForDisplayNumber` 拿不到服务 = 链路彻底断了，macOS 侧没有触发入口
  （既不能 `on`，也不能 probe）。只能物理断电重开显示器 / 拔插视频线 / 换口换线。

### 13.6 2026-11-26 晚确认：sanguang 是整机固件死机，复位必须断电 ≥15 秒

现场操作记录（本次故障的真实恢复过程）：

- 菜单键、电源键全无反应（OSD 弹不出来 → 排除“输入源切错”）；
- 快速插拔电源线无效；
- **拔掉电源线、等 15 秒再插回** → 恢复；同一条视频线、同一个 Mac 口，布局和 75Hz 主屏原样回来；
- 拔掉电源后电源键 LED 还在闪（先彩色、后白色）—— 是电源电容的余电在维持主控。

结论：

- 故障在显示器固件/主控，和 Mac、线、口**无关**（同一根线同一个口，断电复位后完全正常）。
- 复位方法：**拔电源线 ≥15 秒**。如果拔了电源灯还亮/还闪，说明余电没放完，继续等
  （或把视频线也拔掉）。按电源键、快速插拔、显示器开关都不算断电。
- 和 wescom 同属廉价屏 DPMS 唤醒固件问题，但这台表现更狠：整机死机、链路全掉、按键全无响应。
  所以“关显示器电源再开”这类建议对它是无效的，必须拔电源。
