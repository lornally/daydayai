#!/usr/bin/env python3
"""
浙江省地形图生成脚本
- 底图: NASA ASTER GDEM Color Shaded Relief (5000x5000)
- 边界: 阿里云 DataV GeoJSON
- 标注: 浙江精华景点（突出古迹）
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch
from PIL import Image

# 设置中文字体
plt.rcParams['font.family'] = ['Heiti TC', 'PingFang HK', 'Songti SC', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# ==================== 配置 ====================
OUTPUT_PATH = "zhejiang_map.png"
BASE_IMG = "zhejiang_base_5000.jpg"
BOUNDARY_JSON = "zhejiang_boundary.json"

# 底图范围 [west, south, east, north]
WEST, SOUTH, EAST, NORTH = 118.0, 26.5, 122.5, 31.5
IMG_W, IMG_H = 5000, 5000

# 坐标 -> 像素映射
x_scale = IMG_W / (EAST - WEST)
y_scale = IMG_H / (NORTH - SOUTH)

def lonlat_to_pixel(lon, lat):
    x = (lon - WEST) * x_scale
    y = (NORTH - lat) * y_scale
    return x, y

def pixel_to_lonlat(x, y):
    lon = WEST + x / x_scale
    lat = NORTH - y / y_scale
    return lon, lat

# ==================== 景点数据 ====================
# 分类: 古迹(heritage) / 自然(nature)
SITES = [
    # 杭州
    {"name": "西湖", "lon": 120.15, "lat": 30.25, "type": "heritage", "city": "杭州"},
    {"name": "灵隐寺", "lon": 120.10, "lat": 30.24, "type": "heritage", "city": "杭州"},
    {"name": "良渚古城", "lon": 119.98, "lat": 30.42, "type": "heritage", "city": "杭州"},
    {"name": "六和塔", "lon": 120.13, "lat": 30.19, "type": "heritage", "city": "杭州"},
    
    # 绍兴
    {"name": "鲁迅故里", "lon": 120.58, "lat": 29.99, "type": "heritage", "city": "绍兴"},
    {"name": "兰亭", "lon": 120.48, "lat": 29.93, "type": "heritage", "city": "绍兴"},
    {"name": "大禹陵", "lon": 120.52, "lat": 29.98, "type": "heritage", "city": "绍兴"},
    
    # 宁波
    {"name": "天一阁", "lon": 121.55, "lat": 29.87, "type": "heritage", "city": "宁波"},
    {"name": "河姆渡遗址", "lon": 121.38, "lat": 29.97, "type": "heritage", "city": "宁波"},
    
    # 嘉兴
    {"name": "乌镇", "lon": 120.49, "lat": 30.75, "type": "heritage", "city": "嘉兴"},
    {"name": "西塘", "lon": 120.89, "lat": 30.95, "type": "heritage", "city": "嘉兴"},
    {"name": "南湖", "lon": 120.75, "lat": 30.76, "type": "heritage", "city": "嘉兴"},
    
    # 金华
    {"name": "诸葛八卦村", "lon": 119.32, "lat": 29.25, "type": "heritage", "city": "金华"},
    
    # 衢州
    {"name": "孔庙", "lon": 118.87, "lat": 28.97, "type": "heritage", "city": "衢州"},
    {"name": "江郎山", "lon": 118.60, "lat": 28.50, "type": "nature", "city": "衢州"},
    
    # 温州
    {"name": "雁荡山", "lon": 121.07, "lat": 28.37, "type": "nature", "city": "温州"},
    
    # 台州
    {"name": "天台山", "lon": 121.03, "lat": 29.17, "type": "heritage", "city": "台州"},
    {"name": "国清寺", "lon": 121.04, "lat": 29.17, "type": "heritage", "city": "台州"},
    
    # 丽水
    {"name": "缙云仙都", "lon": 120.08, "lat": 28.65, "type": "nature", "city": "丽水"},
    
    # 湖州
    {"name": "南浔古镇", "lon": 120.43, "lat": 30.87, "type": "heritage", "city": "湖州"},
    {"name": "莫干山", "lon": 119.80, "lat": 30.63, "type": "nature", "city": "湖州"},
]

# ==================== 加载边界 ====================
def load_boundary():
    with open(BOUNDARY_JSON, 'r', encoding='utf-8') as f:
        geo = json.load(f)
    
    polygons = []
    for feature in geo.get('features', []):
        geom = feature.get('geometry', {})
        gtype = geom.get('type', '')
        coords = geom.get('coordinates', [])
        
        if gtype == 'Polygon':
            # coords: [exterior_ring, [holes...]]
            exterior = coords[0]
            polygons.append(exterior)
        elif gtype == 'MultiPolygon':
            # coords: [[exterior_ring, [holes...]], ...]
            for poly in coords:
                exterior = poly[0]
                polygons.append(exterior)
    
    return polygons

def simplify_ring(ring, tolerance=0.005):
    """简单的 Douglas-Peucker 风格下采样"""
    if len(ring) <= 10:
        return ring
    result = [ring[0]]
    for i in range(1, len(ring) - 1):
        # 基于距离的下采样
        prev = result[-1]
        curr = ring[i]
        dx = curr[0] - prev[0]
        dy = curr[1] - prev[1]
        dist = (dx*dx + dy*dy) ** 0.5
        if dist > tolerance:
            result.append(curr)
    result.append(ring[-1])
    return result

# ==================== 绘制 ====================
def main():
    print("加载底图...")
    img = Image.open(BASE_IMG)
    img_np = np.array(img)
    print(f"  底图尺寸: {img_np.shape}")
    
    print("加载边界...")
    polygons = load_boundary()
    print(f"  多边形数量: {len(polygons)}")
    
    # 创建画布
    fig, ax = plt.subplots(figsize=(10, 10), dpi=500)
    ax.set_xlim(WEST, EAST)
    ax.set_ylim(SOUTH, NORTH)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 绘制底图
    ax.imshow(img_np, extent=[WEST, EAST, SOUTH, NORTH], origin='upper', interpolation='bilinear')
    
    # 绘制边界（白色+阴影效果）
    print("绘制边界...")
    for ring in polygons:
        ring = simplify_ring(ring, tolerance=0.003)
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        
        # 阴影层
        ax.plot(lons, lats, color='black', linewidth=3, alpha=0.6, solid_capstyle='round')
        # 主体层
        ax.plot(lons, lats, color='white', linewidth=1.5, alpha=0.95, solid_capstyle='round')
    
    # 绘制景点
    print("绘制景点标注...")
    heritage_color = '#FF3333'      # 红色 - 古迹
    nature_color = '#33AA33'        # 绿色 - 自然
    heritage_bg = '#FFE0E0'
    nature_bg = '#E0FFE0'
    
    for site in SITES:
        lon, lat = site['lon'], site['lat']
        color = heritage_color if site['type'] == 'heritage' else nature_color
        bg = heritage_bg if site['type'] == 'heritage' else nature_bg
        
        # 画点
        ax.plot(lon, lat, 'o', color=color, markersize=4, markeredgecolor='white', markeredgewidth=0.8, zorder=5)
        
        # 为每个景点手动指定偏移方向和箭头，避免拥挤
        offsets = {
            # 杭州
            "西湖":         {"dx": 0.06,  "dy": 0.05,  "ha": "left",  "va": "bottom"},
            "灵隐寺":       {"dx": -0.07, "dy": 0.04,  "ha": "right", "va": "bottom"},
            "良渚古城":     {"dx": -0.08, "dy": -0.04, "ha": "right", "va": "top"},
            "六和塔":       {"dx": 0.05,  "dy": -0.06, "ha": "left",  "va": "top"},
            # 绍兴
            "鲁迅故里":     {"dx": 0.07,  "dy": 0.04,  "ha": "left",  "va": "bottom"},
            "兰亭":         {"dx": -0.07, "dy": -0.05, "ha": "right", "va": "top"},
            "大禹陵":       {"dx": 0.05,  "dy": -0.06, "ha": "left",  "va": "top"},
            # 宁波
            "天一阁":       {"dx": -0.07, "dy": 0.04,  "ha": "right", "va": "bottom"},
            "河姆渡遗址":   {"dx": -0.08, "dy": -0.04, "ha": "right", "va": "top"},
            # 嘉兴
            "乌镇":         {"dx": -0.06, "dy": 0.05,  "ha": "right", "va": "bottom"},
            "西塘":         {"dx": 0.06,  "dy": 0.05,  "ha": "left",  "va": "bottom"},
            "南湖":         {"dx": 0.06,  "dy": -0.05, "ha": "left",  "va": "top"},
            # 其他
            "诸葛八卦村":   {"dx": 0.07,  "dy": 0.04,  "ha": "left",  "va": "bottom"},
            "孔庙":         {"dx": 0.06,  "dy": 0.04,  "ha": "left",  "va": "bottom"},
            "江郎山":       {"dx": -0.06, "dy": 0.05,  "ha": "right", "va": "bottom"},
            "雁荡山":       {"dx": -0.07, "dy": -0.04, "ha": "right", "va": "top"},
            "天台山":       {"dx": -0.07, "dy": 0.04,  "ha": "right", "va": "bottom"},
            "国清寺":       {"dx": 0.06,  "dy": -0.05, "ha": "left",  "va": "top"},
            "缙云仙都":     {"dx": 0.06,  "dy": 0.05,  "ha": "left",  "va": "bottom"},
            "南浔古镇":     {"dx": 0.06,  "dy": 0.05,  "ha": "left",  "va": "bottom"},
            "莫干山":       {"dx": -0.07, "dy": 0.04,  "ha": "right", "va": "bottom"},
        }
        
        off = offsets.get(site['name'], {"dx": 0.08, "dy": 0.06, "ha": "left", "va": "bottom"})
        
        ax.annotate(
            site['name'],
            xy=(lon, lat),
            xytext=(lon + off['dx'], lat + off['dy']),
            fontsize=5,
            color='#222222',
            fontweight='bold',
            ha=off['ha'], va=off['va'],
            bbox=dict(boxstyle='round,pad=0.15', facecolor=bg, edgecolor=color, alpha=0.85, linewidth=0.5),
            arrowprops=dict(arrowstyle='-', color=color, lw=0.6),
            zorder=6
        )
    
    # 添加标题
    ax.text(0.5, 0.98, '浙江省地形图', transform=ax.transAxes,
            fontsize=16, fontweight='bold', color='white',
            ha='center', va='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='white', alpha=0.5))
    
    # 添加副标题
    ax.text(0.5, 0.955, 'Zhejiang Province Topographic Map', transform=ax.transAxes,
            fontsize=7, color='white', alpha=0.8, ha='center', va='top')
    
    # 添加图例
    legend_y = 0.04
    ax.plot(0.04, legend_y + 0.04, 'o', color=heritage_color, markersize=5, transform=ax.transAxes, zorder=7)
    ax.text(0.06, legend_y + 0.04, '古迹/人文', transform=ax.transAxes, fontsize=5, color='white', va='center')
    ax.plot(0.18, legend_y + 0.04, 'o', color=nature_color, markersize=5, transform=ax.transAxes, zorder=7)
    ax.text(0.20, legend_y + 0.04, '自然风光', transform=ax.transAxes, fontsize=5, color='white', va='center')
    
    # 数据来源
    ax.text(0.98, 0.01, '数据来源: NASA ASTER GDEM | 底图: Color Shaded Relief',
            transform=ax.transAxes, fontsize=4, color='white', alpha=0.6, ha='right', va='bottom')
    
    plt.tight_layout(pad=0)
    fig.savefig(OUTPUT_PATH, dpi=500, bbox_inches='tight', pad_inches=0.05, facecolor='black')
    plt.close(fig)
    print(f"已保存: {OUTPUT_PATH}")
    
    import os
    fsize = os.path.getsize(OUTPUT_PATH) / 1024 / 1024
    print(f"文件大小: {fsize:.1f} MB")

if __name__ == '__main__':
    main()
