#!/usr/bin/env python3
"""
生成以中国为中心的世界地形图。
三种投影 × 三种地形风格 = 9 张图。
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CENTER_LON = 103.0

# A1 size at 300dpi: 7016 x 4961 px → figure size in inches at 300dpi
DPI = 300
FIG_WIDTH = 7016 / DPI   # ~23.4 inches
FIG_HEIGHT = 4961 / DPI  # ~16.5 inches

PROJECTIONS = {
    "robinson": ccrs.Robinson(central_longitude=CENTER_LON),
    "equalearth": ccrs.EqualEarth(central_longitude=CENTER_LON),
    "mollweide": ccrs.Mollweide(central_longitude=CENTER_LON),
}

STYLES = {
    "hypsometric": {
        "description": "彩色晕渲地形",
        "stock_img": True,
        "ocean_color": None,
        "land_color": None,
    },
    "shaded_relief": {
        "description": "浮雕阴影",
        "stock_img": True,
        "ocean_color": "#1a3a5c",
        "land_color": None,
    },
    "minimal": {
        "description": "简洁地形配色",
        "stock_img": False,
        "ocean_color": "#2b4f72",
        "land_color": "#3d6b35",
    },
}
def make_map(proj_name, proj, style_name, style_config):
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    ax = fig.add_subplot(1, 1, 1, projection=proj)
    ax.set_global()

    if style_config["stock_img"]:
        ax.stock_img()

    if style_config["ocean_color"]:
        ax.add_feature(cfeature.OCEAN, facecolor=style_config["ocean_color"], zorder=1)

    if style_config["land_color"]:
        ax.add_feature(cfeature.LAND, facecolor=style_config["land_color"], zorder=1)

    if style_name == "shaded_relief":
        ax.add_feature(
            cfeature.NaturalEarthFeature("physical", "land", "110m"),
            facecolor="none", edgecolor="none"
        )

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

    # 标注中心点（中国地理中心）
    ax.plot(
        CENTER_LON, 35, "r+", markersize=12, markeredgewidth=2,
        transform=ccrs.PlateCarree(), zorder=5
    )

    plt.tight_layout(pad=0.5)

    filename = f"map_{proj_name}_{style_name}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=DPI, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"  ✓ {filename} ({style_config['description']})")


def main():
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"中心经线: {CENTER_LON}°E")
    print(f"输出分辨率: {DPI}dpi (A1 尺寸)")
    print()

    for proj_name, proj in PROJECTIONS.items():
        print(f"[{proj_name}]")
        for style_name, style_config in STYLES.items():
            make_map(proj_name, proj, style_name, style_config)
        print()

    print("完成！共生成 9 张地图。")


if __name__ == "__main__":
    main()
