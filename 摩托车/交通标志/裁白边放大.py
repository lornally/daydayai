# -*- coding: utf-8 -*-
"""标线图是从国标书上裁的，内容只占中间一条、四周全是白边，所以显示再大也看不清。
这个脚本按“有内容的像素”自动裁掉白边，再等比放大到短边≥700px，让图上的字能看清。
用法：在 交通标志/ 目录下 python3 裁白边放大.py
"""
import os, glob
from PIL import Image

CATS = ['禁止标线', '警告标线', '指示标线', '其他标线']

for cat in CATS:
    for f in sorted(glob.glob(os.path.join(cat, '*.webp'))):
        if os.path.getsize(f) > 900_000:      # 处理过的就别重复处理
            continue
        im = Image.open(f).convert('RGB')
        w, h = im.size
        px = im.load()
        xs, ys = [], []
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                r, g, b = px[x, y]
                if min(r, g, b) < 200:        # 滤掉浅灰水印，保留线条/路面底色/文字
                    xs.append(x); ys.append(y)
        if not xs:
            continue
        x0, x1 = max(min(xs) - 12, 0), min(max(xs) + 12, w)
        y0, y1 = max(min(ys) - 12, 0), min(max(ys) + 12, h)
        cw, ch = x1 - x0, y1 - y0
        im2 = im.crop((x0, y0, x1, y1))
        scale = min(max(700 / max(1, min(cw, ch)), 1.0), 1400 / max(cw, ch))
        if scale > 1.02:
            im2 = im2.resize((int(cw * scale), int(ch * scale)), Image.LANCZOS)
        im2.save(f, 'WEBP', quality=92, method=6)
        print(cat, os.path.basename(f), f"{w}x{h} -> {cw}x{ch} -> {im2.size[0]}x{im2.size[1]}")
