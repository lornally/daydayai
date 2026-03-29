# TextMate 打开 GB 中文文件

## 现象

用 TextMate 打开某些中文文本文件时，会弹出“选择字符集”窗口。
虽然 TextMate 推荐的字符集是对的，比如 `GBK`、`GB2312`、`GB18030`，但“确定”按钮是灰色的，无法点击。

这通常不是文件坏了，而是 TextMate 这个导入流程出了问题。最省心的办法是绕过这个弹窗，先把文件转成 `UTF-8`，再正常打开。

## 最快办法：先转一个文件

已知文件是 GB 系列编码时，直接用 `GB18030` 转码即可。
`GB18030` 兼容 `GBK` 和 `GB2312`，大多数这类中文文本都能正确转成 `UTF-8`。

```sh
iconv -f GB18030 -t UTF-8 "$HOME/Downloads/擒龙.txt" > "$HOME/Downloads/擒龙.utf8.txt"
open -a TextMate "$HOME/Downloads/擒龙.utf8.txt"
```

如果只是临时阅读，不想生成新文件：

```sh
iconv -f GB18030 -t UTF-8 "$HOME/Downloads/擒龙.txt" | less
```

如果只是先看前 40 行：

```sh
iconv -f GB18030 -t UTF-8 "$HOME/Downloads/擒龙.txt" | sed -n '1,40p'
```

## 批量转换下载目录

仓库里的脚本默认会这样做：

1. 递归扫描 `~/Downloads`
2. 跳过非文本文件
3. 跳过已经是 `UTF-8` 的文件
4. 尝试把其余文本按 `GB18030` 转成 `UTF-8`
5. 输出到 `~/Downloads/utf8/`
6. 保留原文件，不覆盖原文件

脚本路径：

```sh
scripts/gb_to_utf8_downloads.sh
```

## 用法

先给脚本执行权限：

```sh
chmod +x scripts/gb_to_utf8_downloads.sh
```

直接处理下载目录：

```sh
./scripts/gb_to_utf8_downloads.sh
```

指定输入目录和输出目录：

```sh
./scripts/gb_to_utf8_downloads.sh "$HOME/Downloads" "$HOME/Desktop/downloads-utf8"
```

## 说明

- 统一用 `GB18030`，是因为它基本可以覆盖 `GBK` / `GB2312`。
- 输出目录和原目录分开，更安全，不会误覆盖原文件。
- 如果脚本提示某个文件转换失败，通常是因为：
  - 它不是 GB 系列文本
  - 它已经是别的编码
  - 它根本不是文本文件
- 转完以后，用 TextMate、VS Code、BBEdit、macOS 自带文本工具打开 `UTF-8` 版本都更稳。

## 结论

如果 TextMate 的字符集确认按钮点不了，不必卡在那个弹窗里。
先用 `iconv` 转成 `UTF-8`，再打开，是最稳、最快、最少折腾的办法。
