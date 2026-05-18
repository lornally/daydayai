#!/usr/bin/env python3
"""
生成以中国为中心的世界地形图（v3 - 斜轴投影）。
通过旋转地球坐标实现任意点居中，再套用 Robinson/EqualEarth/Mollweide 投影。
完整地球，无裁剪。
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
from matplotlib.image import imread
from scipy.ndimage import map_coordinates
from pathlib import Path

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

DPI = 300
FIG_WIDTH = 7016 / DPI
FIG_HEIGHT = 4961 / DPI

CENTERS = {
    "china": {"lon": 103.0, "lat": 35.0, "label": "中国地理中心"},
    "beijing": {"lon": 116.4, "lat": 39.9, "label": "北京"},
}

PROJECTION_TYPES = ["robinson", "equalearth", "mollweide"]

STYLES = ["hypsometric", "relief_dark", "relief_ocean"]


def rotate_point(lon, lat, center_lon, center_lat):
    lon_r = np.radians(np.asarray(lon, dtype=float))
    lat_r = np.radians(np.asarray(lat, dtype=float))
    clon = np.radians(center_lon)
    clat = np.radians(center_lat)

    x = np.cos(lat_r) * np.cos(lon_r - clon)
    y = np.cos(lat_r) * np.sin(lon_r - clon)
    z = np.sin(lat_r)

    cos_a = np.cos(clat)
    sin_a = np.sin(clat)
    x_new = x * cos_a + z * sin_a
    z_new = -x * sin_a + z * cos_a

    new_lat = np.degrees(np.arcsin(np.clip(z_new, -1, 1)))
    new_lon = np.degrees(np.arctan2(y, x_new))
    return new_lon, new_lat

def rotate_raster(img, center_lon, center_lat):
    """旋转栅格图像（stock_img），使 center 点变成 (0,0)"""
    h, w = img.shape[:2]
    # 生成输出图像的经纬度网格（标准 PlateCarree）
    out_lons = np.linspace(-180, 180, w)
    out_lats = np.linspace(90, -90, h)
    out_lon_grid, out_lat_grid = np.meshgrid(out_lons, out_lats)

    # 反向旋转：从输出坐标找到原始坐标
    inv_lon, inv_lat = rotate_point(
        out_lon_grid, out_lat_grid, -center_lon, -center_lat
    )
    # 修正：反向旋转需要先绕Y轴反转再平移经度
    # 直接用正向旋转的逆运算
    lon_r = np.radians(out_lon_grid)
    lat_r = np.radians(out_lat_grid)
    clat = np.radians(center_lat)
    clon = np.radians(center_lon)

    x = np.cos(lat_r) * np.cos(lon_r)
    y = np.cos(lat_r) * np.sin(lon_r)
    z = np.sin(lat_r)

    # 反向绕Y轴旋转 +clat
    cos_a = np.cos(-clat)
    sin_a = np.sin(-clat)
    x_orig = x * cos_a + z * sin_a
    z_orig = -x * sin_a + z * cos_a
    y_orig = y

    orig_lat = np.degrees(np.arcsin(np.clip(z_orig, -1, 1)))
    orig_lon = np.degrees(np.arctan2(y_orig, x_orig)) + center_lon
    # 归一化经度到 [-180, 180]
    orig_lon = (orig_lon + 180) % 360 - 180

    # 将经纬度转为图像像素坐标
    col = (orig_lon + 180) / 360 * (w - 1)
    row = (90 - orig_lat) / 180 * (h - 1)

    # 双线性插值采样
    if img.ndim == 3:
        rotated = np.zeros_like(img)
        for c in range(img.shape[2]):
            rotated[:, :, c] = map_coordinates(
                img[:, :, c], [row, col], order=1, mode='wrap'
            )
    else:
        rotated = map_coordinates(img, [row, col], order=1, mode='wrap')

    return rotated


def split_line_at_dateline(coords, threshold=150):
    """在跨越日期变更线处断开线段"""
    segments = []
    current = [coords[0]]
    for i in range(1, len(coords)):
        if abs(coords[i][0] - coords[i-1][0]) > threshold:
            if len(current) > 1:
                segments.append(np.array(current))
            current = [coords[i]]
        else:
            current.append(coords[i])
    if len(current) > 1:
        segments.append(np.array(current))
    return segments

def get_projection(proj_type):
    if proj_type == "robinson":
        return ccrs.Robinson(central_longitude=0)
    elif proj_type == "equalearth":
        return ccrs.EqualEarth(central_longitude=0)
    elif proj_type == "mollweide":
        return ccrs.Mollweide(central_longitude=0)


def draw_rotated_features(ax, center_lon, center_lat, style):
    """绘制旋转后的地理要素"""
    pc = ccrs.PlateCarree()

    # 加载并绘制海岸线
    for category, name, color, lw in [
        ("physical", "coastline", "#333333", 0.5),
        ("cultural", "admin_0_boundary_lines_land", "#666666", 0.3),
    ]:
        shp_path = shpreader.natural_earth(resolution='110m', category=category, name=name)
        reader = shpreader.Reader(shp_path)
        for geom in reader.geometries():
            if hasattr(geom, 'geoms'):
                lines = list(geom.geoms)
            else:
                lines = [geom]
            for line in lines:
                coords = np.array(line.coords)
                rot_lon, rot_lat = rotate_point(coords[:, 0], coords[:, 1], center_lon, center_lat)
                rotated = np.column_stack([rot_lon, rot_lat])
                segments = split_line_at_dateline(rotated)
                for seg in segments:
                    ax.plot(seg[:, 0], seg[:, 1], color=color, linewidth=lw,
                            transform=pc, zorder=3)


def make_map(proj_name, proj, style, center_lon, center_lat, center_key):
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    ax = fig.add_subplot(1, 1, 1, projection=proj)
    ax.set_global()
    ax.set_facecolor('black' if style == 'relief_dark' else 'white')

    import cartopy
    stock_path = os.path.join(os.path.dirname(cartopy.__file__), 'data', 'raster', 'natural_earth',
                              '50-natural-earth-1-downsampled.png')
    img = imread(stock_path)

    rotated_img = rotate_raster(img, center_lon, center_lat)

    if style == 'relief_dark':
        # 黑色为主的浮雕：深海最黑，高山最白
        gray = np.mean(rotated_img[:, :, :3], axis=2)
        gray = np.clip(gray * 1.3, 0, 1)
        rotated_img = np.stack([gray, gray, gray], axis=2)
    elif style == 'relief_ocean':
        # 灰度浮雕 + 保留海洋蓝色
        gray = np.mean(rotated_img[:, :, :3], axis=2)
        # 检测海洋区域（原图中蓝色主导的像素）
        r, g, b = rotated_img[:, :, 0], rotated_img[:, :, 1], rotated_img[:, :, 2]
        ocean_mask = (b > r + 0.05) & (b > g + 0.02)
        # 陆地用灰度
        result = np.stack([gray, gray, gray], axis=2)
        # 海洋保留原色（稍微加深）
        result[ocean_mask] = rotated_img[ocean_mask][:, :3] * 0.85
        rotated_img = result

    ax.imshow(rotated_img, origin='upper', transform=ccrs.PlateCarree(),
              extent=[-180, 180, -90, 90], zorder=1)

    draw_rotated_features(ax, center_lon, center_lat, style)

    # 网格线
    gl = ax.gridlines(linewidth=0.3, color='gray', alpha=0.5, linestyle='--', zorder=4)

    # 中心标记
    ax.plot(0, 0, 'r+', markersize=12, markeredgewidth=2, transform=ccrs.PlateCarree(), zorder=5)

    filename = f"map_v3_{center_key}_{proj_name}_{style}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=DPI, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    print(f"  ✓ {filename}")


def main():
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"输出分辨率: {DPI}dpi (A1 尺寸)")
    print()

    total = 0
    for center_key, center_info in CENTERS.items():
        clon, clat = center_info["lon"], center_info["lat"]
        print(f"=== {center_info['label']} ({clon}°E, {clat}°N) ===")
        for proj_name in PROJECTION_TYPES:
            proj = get_projection(proj_name)
            print(f"  [{proj_name}]")
            for style in STYLES:
                make_map(proj_name, proj, style, clon, clat, center_key)
                total += 1
        print()

    print(f"完成！共生成 {total} 张地图。")


if __name__ == "__main__":
    main()
