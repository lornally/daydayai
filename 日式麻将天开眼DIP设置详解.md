# 天开眼 (tenkai) DIP 设置详解

本文基于本机 `MAME v0.285` 的 `mame -listxml tenkai`。
下面尽量只写已经能确认的内容；名字看得懂但效果没法百分百验证的地方，会单独注明。

## DIP Switches 是什么

DIP Switches 是街机主板上的物理拨码开关。
在 MAME 里可以在游戏中按 `Tab`，进入 `DIP Switches` 菜单修改。

## 已确认的 DIP 项

### DSW0

| 项目 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `Payout Rate` | `50%` 到 `96%` | `71%` | 返还率/出分率，不是“配牌率” |
| `Odds Rate` | `1 2 4 8 12 16 24 32` / `1 2 3 5 8 15 30 50` / `1 2 3 5 10 25 50 100` / `1 2 3 5 10 50 100 200` | `1 2 3 5 8 15 30 50` | 倍率表 |
| `Maximum Bet` | `1` / `5` / `10` / `20` | `10` | 最大下注 |

### DSW1

| 项目 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `Coinage` | `1 Coin/1 Credit` / `1 Coin/2 Credits` / `1 Coin/5 Credits` / `1 Coin/10 Credits` | `1 Coin/1 Credit` | 投币比率 |
| `Minimum Bet` | `1` / `2` / `3` / `5` | `1` | 最低下注 |
| `Yakuman Bonus Cycle` | `None` / `First time only` / `Every 300 coins` / `Every 500 coins` / `Every 700 coins` / `Every 1000 coins` | `Every 500 coins` | 役满奖励出现周期 |
| `Yakuman Bonuses Per Cycle` | `1` / `2` | `1` | 每个周期给几次役满奖励 |

### DSW2

| 项目 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `Payout Mode` | `Key-out` / `Hopper` | `Key-out` | 出分方式 |
| `Hopper Polarity` | `Normal` / `Inverted` | `Normal` | 退币器信号极性，只在 `Hopper` 模式下比较有意义 |
| `Tenkaigen Day` | `Off` / `On` | `On` | 具体效果未确认 |
| `Double Bet` | `Off` / `On` | `On` | 是否允许双倍玩法 |
| `Renchan Rate` | `Off` / `On` | `On` | 名字像“连庄相关”，精确效果未确认 |
| `Auto Reach` | `Off` / `On` | `On` | 自动立直/听牌相关选项 |
| `Last Chance` | `Off` / `On` | `On` | 最后机会相关选项 |
| `Don Den Button` | `Start` / `Flip Flop` | `Flip Flop` | 设定 `Don Den` 用哪个按钮触发 |

### DSW3

| 项目 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `Demo Sounds` | `Off` / `On` | `On` | 演示声音 |
| `In-Game Music` | `Off` / `On` | `On` | 游戏音乐 |
| `Gal Select` | `Off` / `On` | `On` | 具体效果未完全确认 |
| `Gal Pose` | `Type A` / `Type B` | `Type A` | 奖励画面类型 |
| `Demo Message Language` | `Japanese` / `Taiwan` | `Japanese` | 演示文字语言 |
| `SP Express Frequency` | `Low` / `Normal` | `Normal` | 特殊演出频率 |
| `Tenkaigen Day Frequency` | `Low` / `Normal` | `Normal` | 天开眼日出现频率 |
| `Time Settings Mode` | `Off` / `On` | `Off` | 时间设置模式 |

### DSW4

| 项目 | 可选值 | 默认值 | 说明 |
|------|--------|--------|------|
| `Credits Per Note` | 会随 `Coinage` 改变 | 依 `Coinage` 而定 | 纸币投入对应多少 credits |
| `Flip Screen` | `Off` / `On` | `Off` | 画面翻转 |
| `Computer Strength` | `Normal` / `Strong` | `Normal` | 电脑强度，没有 `Weak` |
| `Service Count` | `Off` / `On` | `On` | 精确效果未确认 |
| `Don Den Count` | `5 times` / `8 times` | `8 times` | `Don Den` 可用次数 |
| `Show In-Game Clock` | `No` / `Yes` | `Yes` | 显示游戏内时钟 |
| `Game Title` | `Mahjong Tenkaigen` / `Mahjong Tenkaigen Part 2` | `Mahjong Tenkaigen` | 标题版本切换 |

## 关于 SW4-10

最后一个开关会随 `Game Title` 改名：

- 当 `Game Title = Mahjong Tenkaigen` 时，它显示为 `Unknown`
- 当 `Game Title = Mahjong Tenkaigen Part 2` 时，它显示为 `Show Yakuman Table`

也就是说，`Show Yakuman Table` 不是一直都能看到的。

## 推荐配置

如果只是想轻松玩、少折腾，可以先试：

| 设置 | 推荐值 | 理由 |
|------|--------|------|
| `Payout Rate` | `90%` 到 `96%` | 更耐玩，但这不是“更容易发好牌” |
| `Odds Rate` | `1 2 3 5 10 50 100 200` | 倍率更激进 |
| `Minimum Bet` | `1` | 压力小 |
| `Maximum Bet` | `10` | 默认就够用 |
| `Yakuman Bonus Cycle` | `Every 300 coins` | 奖励更常见 |
| `Yakuman Bonuses Per Cycle` | `2` | 每周期奖励更多 |
| `Payout Mode` | `Key-out` | 在 MAME 里通常更省事 |
| `Auto Reach` | `On` | 减少操作 |
| `Last Chance` | `On` | 开着更友好 |
| `Computer Strength` | `Normal` | 已经是最简单选项，没有 `Weak` |
| `Game Title` | `Mahjong Tenkaigen Part 2` | 这样才会出现 `Show Yakuman Table` |
| `Show Yakuman Table` | `Yes` | 方便查表 |

## 如何修改 DIP 设置

```text
1. 游戏中按 Tab
2. 选择 "DIP Switches"
3. 用方向键移动
4. 按左/右切换选项
5. 按 Esc 退出，MAME 会保存设置
