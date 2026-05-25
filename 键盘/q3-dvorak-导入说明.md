## Q3 Dvorak Keymap 导入说明

### 关键发现：Keychron Launcher 的真实格式

我看了你下载的 `Keymap-K2 HE ANSI-25-14-28.json`，Keychron Launcher 的格式和之前另一个 AI 生成的完全不同！

真实格式是数值型的：
```json
{
  "id": 875826720,
  "keymap": [
    [
      {"col": 0, "row": 0, "val": 41},
      {"col": 1, "row": 0, "val": 58},
      ...
    ],
    ...
  ],
  "version": "1.0.0",
  "MD5": "..."
}
```

- 每个键用 `{col, row, val}` 表示，基于硬件矩阵位置
- `val` 是数字键码，不是字符串（如 `KC_ESC` 对应 `41`）
- 之前 AI 生成的 `q3-dvorak.json` 用的是字符串名 + 错误格式，**完全无法导入**

### 下载按钮没反应的解决办法

你说人肉点好了但下载按钮没反应，可以试试：

1. **换浏览器** — 优先用 Chrome 或 Edge，Safari 可能兼容性差
2. **无痕模式** — Chrome 的 `Cmd+Shift+N` 新开无痕窗口再试
3. **清缓存** — 清除 `launcher.keychron.com` 的缓存和 Cookie
4. **检查控制台** — 按 `F12` → `Console`，点击下载按钮看有没有红色报错，有的话截图给我
5. **确保有线连接** — 蓝牙模式下可能某些功能受限

### 如果下载确实坏了：从浏览器提取当前配置

如果你已经手动点好了 Dvorak，数据还在浏览器内存里，可以强行拷出来：

1. 在 Keychron Launcher 页面按 `F12` 打开开发者工具
2. 切换到 **Console（控制台）** 标签
3. 粘贴下面的代码并按回车：

```javascript
// 尝试从页面中提取当前 keymap
(function(){
  // 方法1: 搜索全局变量
  for (let k in window) {
    try {
      let v = window[k];
      if (v && typeof v === 'object' && v.keymap && Array.isArray(v.keymap) && v.keymap.length >= 2) {
        console.log('Found keymap in window.' + k);
        copy(JSON.stringify(v, null, 2));
        console.log('已复制到剪贴板！');
        return;
      }
    } catch(e) {}
  }
  // 方法2: 搜索 angular/react 组件树
  let roots = document.querySelectorAll('[ng-version], [data-reactroot]');
  console.log('Found', roots.length, 'app roots');
  // 方法3: 直接导出 localStorage / sessionStorage
  for (let store of [localStorage, sessionStorage]) {
    for (let i = 0; i < store.length; i++) {
      let key = store.key(i);
      let val = store.getItem(key);
      if (val && val.includes('keymap')) {
        console.log('Found in', store === localStorage ? 'localStorage' : 'sessionStorage', 'key=' + key);
        try {
          let data = JSON.parse(val);
          if (data.keymap || (Array.isArray(data) && data[0] && data[0].val)) {
            copy(JSON.stringify(data, null, 2));
            console.log('已复制到剪贴板！');
            return;
          }
        } catch(e) {}
      }
    }
  }
  console.log('自动搜索没找到，请把当前页面 URL 和截图发给我再分析');
})();
```

4. 如果成功，JSON 数据会复制到你的剪贴板，粘贴保存成 `.json` 文件即可

### 备用方案：直接导入我生成的 JSON

如果你不想折腾浏览器，我已经基于 Keychron Launcher 的真实格式生成了 Q3 ANSI Dvorak keymap：

**文件：`q3-dvorak-keychron-launcher.json`**

- 格式完全匹配 Keychron Launcher 的导出格式（`{col, row, val}`）
- 87 键，4 层（Mac Base Dvorak / Mac Fn / Windows Base Dvorak / Windows Fn）
- 键码值从 Keychron Launcher 的 JS 源码中反解出来的，应该准确

**导入步骤：**
1. 打开 https://launcher.keychron.com/#/keymap
2. 用数据线连接 Q3 键盘
3. 点击 **Import Keymap**
4. 选择 `q3-dvorak-keychron-launcher.json`
5. 点击 **Save** 写入键盘

### 层说明

| 层 | 说明 |
|----|------|
| 层 0 | **Mac Base Dvorak** — 主键区 Dvorak，修饰键为 Mac 布局 (Option/Cmd) |
| 层 1 | **Mac Fn** — Fn 层（F1-F12、RGB 控制、NKRO 切换） |
| 层 2 | **Windows Base Dvorak** — 主键区 Dvorak，修饰键为 Win 布局 (Alt/Win) |
| 层 3 | **Windows Fn** — Fn 层 |

Fn 键位置：
- Mac Base（层0）：`MO(1)` 切换到 Mac Fn
- Windows Base（层2）：`MO(3)` 切换到 Windows Fn
