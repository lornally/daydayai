# os27 专用（不要和 os15 的共享脚本混用）

os27 = Mac Studio (M1 Max)，三块屏：WSM `C3273IUY`、PHL 438P1、MSI PS341WU。

## 2026-11-28 关键发现：黑屏可以用整机睡眠→完整唤醒恢复

WSM 卡死时的状态：DDC 全部失败，CG 里只剩一个空壳（无 EDID、无模式），
软件接回 / 软件拔插 / HiDPI↔1x / 显示睡眠 全部无效。

**有效恢复：整机睡眠 → 完整唤醒。** 已验证一次：

- `pmset sleepnow` 进入 Sleep；
- DarkWake 之后用 `caffeinate -u -t 10` 触发 FullWake（只 DarkWake 不够，显示器不会亮）；
- 唤醒后 WSM 自动重新枚举，DDC 读到 50，布局和窗口都不受影响。

命令：

```bash
fix-wescom-os27 --sleep-wake     # 自动做上面的睡眠+唤醒并验证 DDC
fix-wescom-os27                  # 只读诊断
fix-wescom-os27 --save           # 保存当前布局
fix-wescom-os27 --restore        # 恢复布局（WSM 黑屏时拒绝执行）
```

## 看护的边界

`wescom-watchdog-os27` 只读 DDC 检测；卡死时唯一动作是用 `wescom-dpfix off`
把黑屏移出桌面，让窗口退回可用屏，然后通知。**不会自动整机睡眠**，也不会改分辨率/布局/主屏。

## 安装

```bash
./install-os27.sh
```

会把本目录的脚本装到 `~/.local/bin/`，并让本机旧名字 `fix-wescom` / `wescom-watchdog`
也指向 os27 版本；os15 的共享脚本保持原样，不要在 os27 上运行它们。
