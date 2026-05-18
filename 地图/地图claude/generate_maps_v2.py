#!/usr/bin/env python3
"""
生成以中国为中心的世界地形图（第二批，修正版）。
三种投影 × 两种地形风格 × 两个中心点 = 12 张图。
纵向居中到目标纬度。
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

DPI = 300
FIG_WIDTH = 7016 / DPI
FIG_HEIGHT = 4961 / DPI

CENTERS = {
    "china": {"lon": 103.0, "lat": 35.0, "label": "中国地理中心"},
    "beijing": {"lon": 116.4, "lat": 39.9, "label": "北京"},
}

PROJECTION_TYPES = ["robinson", "equalearth", "mollweide"]

STYLES = {
    "hypsometric": {
        "description": "彩色晕渲地形",
        "stock_img": True,
        "ocean_color": None,
    },
    "shaded_relief": {
        "description": "浮雕阴影",
        "stock_img": True,
        "ocean_color": "#1a3a5c",
    },
}


def get_projection(proj_type, center_lon):
    if proj_type == "robinson":
        return ccrs.Robinson(central_longitude=center_lon)
    elif proj_type == "equalearth":
        return ccrs.EqualEarth(central_longitude=center_lon)
    elif proj_type == "mollweide":
        return ccrs.Mollweide(central_longitude=center_lon)


def make_map(proj_name, proj, style_name, style_config, center_lon, center_lat, center_key):
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    ax = fig.add_subplot(1, 1, 1, projection=proj)
    ax.set_global()
    # 纵向居中：计算目标纬度在投影坐标系中的 y 值，然后对称裁剪
    target_xy = proj.transform_point(center_lon, center_lat, ccrs.PlateCarree())
    target_y = target_xy[1]

    # 获取投影的完整 y 范围
    north_xy = proj.transform_point(center_lon, 90, ccrs.PlateCarree())
    south_xy = proj.transform_point(center_lon, -90, ccrs.PlateCarree())
    y_max = north_xy[1]
    y_min = south_xy[1]

    # 以 target_y 为中心，取能容纳的最大对称范围
    dist_to_top = y_max - target_y
    dist_to_bottom = target_y - y_min
    half_range = min(dist_to_top, dist_to_bottom)

    ax.set_ylim(target_y - half_range, target_y + half_range)

    if style_config["stock_img"]:
        ax.stock_img()

    if style_config["ocean_color"]:
        ax.add_feature(cfeature.OCEAN, facecolor=style_config["ocean_color"], zorder=1)

    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor="#333333", zorder=3)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, edgecolor="#666666", zorder=3)
    ax.add_feature(cfeature.RIVERS, linewidth=0.3, edgecolor="#4a90d9", zorder=2)
    ax.add_feature(cfeature.LAKES, facecolor="#4a90d9", edgecolor="none", zorder=2)

    gl = ax.gridlines(
        draw_labels=False,
        linewidth=0.3,
        color="gray",
        alpha=0.5,
        linestyle="--",
    )
    gl.xlocator = plt.FixedLocator(range(-180, 181, 30))
    gl.ylocator = plt.FixedLocator(range(-90, 91, 30))

    ax.plot(
        center_lon, center_lat, "r+", markersize=12, markeredgewidth=2,
        transform=ccrs.PlateCarree(), zorder=5
    )

    plt.tight_layout(pad=0.5)

    filename = f"map_v2_{center_key}_{proj_name}_{style_name}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=DPI, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"  ✓ {filename}")


def main():
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"输出分辨率: {DPI}dpi (A1 尺寸)")
    print()

    total = 0
    for center_key, center_info in CENTERS.items():
        print(f"=== {center_info['label']} ({center_info['lon']}°E, {center_info['lat']}°N) ===")
        for proj_name in PROJECTION_TYPES:
            proj = get_projection(proj_name, center_info["lon"])
            print(f"  [{proj_name}]")
            for style_name, style_config in STYLES.items():
                make_map(
                    proj_name, proj, style_name, style_config,
                    center_info["lon"], center_info["lat"], center_key
                )
                total += 1
        print()

    print(f"完成！共生成 {total} 张地图。")


if __name__ == "__main__":
    main()
