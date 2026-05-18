#!/usr/bin/env python3
"""
v4: 用 ETOPO 2022 DEM 数据生成高质量世界地形图。
斜轴投影，中国居中，非线性颜色映射。
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import netCDF4 as nc
from scipy.ndimage import map_coordinates
from matplotlib.image import imread

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
ETOPO_PATH = os.path.join(OUTPUT_DIR, "ETOPO_2022_v1_60s.nc")

DPI = 300
FIG_WIDTH = 7016 / DPI
FIG_HEIGHT = 4961 / DPI

CENTERS = {
    "china": {"lon": 103.0, "lat": 35.0, "label": "中国地理中心"},
    "beijing": {"lon": 116.4, "lat": 39.9, "label": "北京"},
}

PROJECTION_TYPES = ["robinson", "equalearth", "mollweide"]
STYLES = ["hypsometric", "relief_dark", "relief_ocean"]


def load_etopo():
    """加载 ETOPO DEM 数据"""
    ds = nc.Dataset(ETOPO_PATH)
    z = ds.variables['z'][:]  # shape: (10800, 21600)
    ds.close()
    return z.astype(np.float32)


def rotate_raster_dem(dem, center_lon, center_lat, out_h=5400, out_w=10800):
    """旋转 DEM 栅格，使 center 点变成 (0,0)"""
    out_lons = np.linspace(-180, 180, out_w, endpoint=False)
    out_lats = np.linspace(90, -90, out_h, endpoint=False)
    out_lon_grid, out_lat_grid = np.meshgrid(out_lons, out_lats)

    lon_r = np.radians(out_lon_grid)
    lat_r = np.radians(out_lat_grid)
    clat = np.radians(center_lat)
    clon = np.radians(center_lon)
    # 反向旋转：从输出坐标找原始坐标
    x = np.cos(lat_r) * np.cos(lon_r)
    y = np.cos(lat_r) * np.sin(lon_r)
    z = np.sin(lat_r)

    cos_a = np.cos(-clat)
    sin_a = np.sin(-clat)
    x_orig = x * cos_a + z * sin_a
    z_orig = -x * sin_a + z * cos_a

    orig_lat = np.degrees(np.arcsin(np.clip(z_orig, -1, 1)))
    orig_lon = np.degrees(np.arctan2(y, x_orig)) + center_lon
    orig_lon = (orig_lon + 180) % 360 - 180

    # 转为像素坐标（ETOPO 数据 lat 从 -90 到 90，即 row 0 = 南极）
    h, w = dem.shape
    col = (orig_lon + 180) / 360 * (w - 1)
    row = (orig_lat + 90) / 180 * (h - 1)

    rotated = map_coordinates(dem, [row, col], order=1, mode='wrap')
    return rotated


def elevation_to_dark(elev):
    """非线性映射：深海=黑，平原=深灰(#333)，高山=白
    -10752m -> 0.0 (纯黑)
    0m -> 0.2 (#333333)
    1000m -> 0.35
    3000m -> 0.55
    5000m -> 0.75
    8000m+ -> 1.0 (纯白)
    """
    result = np.zeros_like(elev, dtype=np.float32)

    # 海洋部分：-10752 到 0 -> 0.0 到 0.15
    ocean = elev < 0
    result[ocean] = 0.15 * (1 + elev[ocean] / 10752)

    # 陆地部分：0 到 8157 -> 0.2 到 1.0，用幂函数使高山才亮
    land = elev >= 0
    normalized = np.clip(elev[land] / 8200, 0, 1)
    result[land] = 0.2 + 0.8 * (normalized ** 0.5)

    return result


def elevation_to_hypsometric(elev):
    """彩色地形：陆地无蓝色，海洋深蓝到黑"""
    ocean_colors = [
        (-10752, (0.0, 0.0, 0.02)),      # 最深海 - 近纯黑
        (-6000, (0.02, 0.04, 0.12)),
        (-3000, (0.04, 0.08, 0.20)),
        (-1000, (0.06, 0.12, 0.28)),
        (-200, (0.08, 0.15, 0.32)),
        (0, (0.10, 0.18, 0.35)),          # 浅海 - 仍然是深蓝
    ]
    land_colors = [
        (0, (0.15, 0.38, 0.18)),          # 低地绿
        (200, (0.25, 0.50, 0.22)),
        (500, (0.45, 0.55, 0.25)),
        (1000, (0.60, 0.55, 0.25)),
        (2000, (0.65, 0.45, 0.20)),
        (3000, (0.55, 0.35, 0.18)),       # 高原棕
        (4500, (0.50, 0.30, 0.20)),
        (6000, (0.70, 0.65, 0.60)),       # 高山灰
        (8200, (1.0, 1.0, 1.0)),           # 雪山白
    ]

    h, w = elev.shape
    rgb = np.zeros((h, w, 3), dtype=np.float32)

    # 海洋
    for i in range(len(ocean_colors) - 1):
        e0, c0 = ocean_colors[i]
        e1, c1 = ocean_colors[i + 1]
        mask = (elev >= e0) & (elev < e1)
        if mask.any():
            t = (elev[mask] - e0) / (e1 - e0)
            for ch in range(3):
                rgb[:, :, ch][mask] = c0[ch] + t * (c1[ch] - c0[ch])

    # 陆地
    for i in range(len(land_colors) - 1):
        e0, c0 = land_colors[i]
        e1, c1 = land_colors[i + 1]
        mask = (elev >= e0) & (elev < e1)
        if mask.any():
            t = (elev[mask] - e0) / (e1 - e0)
            for ch in range(3):
                rgb[:, :, ch][mask] = c0[ch] + t * (c1[ch] - c0[ch])

    # 最高处
    mask = elev >= 8200
    rgb[mask] = [1.0, 1.0, 1.0]

    return np.clip(rgb, 0, 1)

def elevation_to_relief_ocean(elev):
    """陆地灰度浮雕 + 海洋保留蓝色深度"""
    h, w = elev.shape
    rgb = np.zeros((h, w, 3), dtype=np.float32)

    # 海洋：蓝色深度
    ocean = elev < 0
    depth_norm = np.clip(-elev[ocean] / 10752, 0, 1)
    rgb[:, :, 0][ocean] = 0.05 + 0.15 * (1 - depth_norm)
    rgb[:, :, 1][ocean] = 0.10 + 0.25 * (1 - depth_norm)
    rgb[:, :, 2][ocean] = 0.25 + 0.45 * (1 - depth_norm)

    # 陆地：灰度，低地暗，高山亮
    land = elev >= 0
    normalized = np.clip(elev[land] / 8200, 0, 1)
    gray = 0.25 + 0.75 * (normalized ** 0.45)
    rgb[:, :, 0][land] = gray
    rgb[:, :, 1][land] = gray
    rgb[:, :, 2][land] = gray

    return np.clip(rgb, 0, 1)


def split_line_at_dateline(coords, threshold=150):
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


def draw_rotated_features(ax, center_lon, center_lat):
    pc = ccrs.PlateCarree()
    for category, name, color, lw in [
        ("physical", "coastline", "#222222", 0.4),
        ("cultural", "admin_0_boundary_lines_land", "#555555", 0.25),
    ]:
        shp_path = shpreader.natural_earth(resolution='110m', category=category, name=name)
        reader = shpreader.Reader(shp_path)
        for geom in reader.geometries():
            lines = list(geom.geoms) if hasattr(geom, 'geoms') else [geom]
            for line in lines:
                coords = np.array(line.coords)
                rot_lon, rot_lat = rotate_point(coords[:, 0], coords[:, 1], center_lon, center_lat)
                rotated = np.column_stack([rot_lon, rot_lat])
                for seg in split_line_at_dateline(rotated):
                    ax.plot(seg[:, 0], seg[:, 1], color=color, linewidth=lw,
                            transform=pc, zorder=3)


def get_projection(proj_type):
    if proj_type == "robinson":
        return ccrs.Robinson(central_longitude=0)
    elif proj_type == "equalearth":
        return ccrs.EqualEarth(central_longitude=0)
    elif proj_type == "mollweide":
        return ccrs.Mollweide(central_longitude=0)

def make_map(proj_name, proj, style, center_lon, center_lat, center_key, dem):
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    ax = fig.add_subplot(1, 1, 1, projection=proj)
    ax.set_global()
    ax.set_facecolor('black')

    rotated_dem = rotate_raster_dem(dem, center_lon, center_lat)

    if style == 'relief_dark':
        img = elevation_to_dark(rotated_dem)
        rgb = np.stack([img, img, img], axis=2)
    elif style == 'hypsometric':
        rgb = elevation_to_hypsometric(rotated_dem)
    elif style == 'relief_ocean':
        rgb = elevation_to_relief_ocean(rotated_dem)

    ax.imshow(rgb, origin='upper', transform=ccrs.PlateCarree(),
              extent=[-180, 180, -90, 90], zorder=1, interpolation='bilinear')

    draw_rotated_features(ax, center_lon, center_lat)

    gl = ax.gridlines(linewidth=0.2, color='gray', alpha=0.4, linestyle='--', zorder=4)

    ax.plot(0, 0, 'r+', markersize=10, markeredgewidth=1.5,
            transform=ccrs.PlateCarree(), zorder=5)

    filename = f"map_v4_{center_key}_{proj_name}_{style}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=DPI, bbox_inches='tight', pad_inches=0.1,
                facecolor='black')
    plt.close(fig)
    print(f"  ✓ {filename}")


def main():
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"输出分辨率: {DPI}dpi (A1 尺寸)")
    print("加载 ETOPO 2022 DEM 数据...")
    dem = load_etopo()
    print(f"  DEM shape: {dem.shape}, range: {dem.min():.0f}m ~ {dem.max():.0f}m")
    print()

    total = 0
    for center_key, center_info in CENTERS.items():
        clon, clat = center_info["lon"], center_info["lat"]
        print(f"=== {center_info['label']} ({clon}°E, {clat}°N) ===")
        for proj_name in PROJECTION_TYPES:
            proj = get_projection(proj_name)
            print(f"  [{proj_name}]")
            for style in STYLES:
                make_map(proj_name, proj, style, clon, clat, center_key, dem)
                total += 1
        print()

    print(f"完成！共生成 {total} 张地图。")


if __name__ == "__main__":
    main()
