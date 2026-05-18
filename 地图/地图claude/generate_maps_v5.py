#!/usr/bin/env python3
"""
v5: Natural Earth 2 颜色 + DEM hillshade + 高程覆盖。
- 低海拔：用 Natural Earth 2 的真实地表颜色（森林绿、沙漠黄、草原浅绿）
- 高海拔：用 DEM 高程色带（高原棕→高山灰→雪山白）渐变覆盖
- 全部叠加 hillshade 做立体感
- 海洋：DEM 深度 → 深蓝到黑色
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import netCDF4 as nc
from scipy.ndimage import map_coordinates
from PIL import Image

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
ETOPO_PATH = os.path.join(OUTPUT_DIR, "ETOPO_2022_v1_60s.nc")
NE2_PATH = os.path.join(OUTPUT_DIR, "NE2_raster", "NE2_50M_SR_W", "NE2_50M_SR_W.tif")

DPI = 300
FIG_WIDTH = 7016 / DPI
FIG_HEIGHT = 4961 / DPI

MAPS_TO_GENERATE = [
    {"center_key": "beijing", "lon": 116.4, "lat": 39.9, "proj": "robinson"},
    {"center_key": "china", "lon": 103.0, "lat": 35.0, "proj": "equalearth"},
]


def load_etopo():
    ds = nc.Dataset(ETOPO_PATH)
    z = ds.variables['z'][:].astype(np.float32)
    ds.close()
    return z


def load_ne2():
    img = Image.open(NE2_PATH)
    return np.array(img).astype(np.float32) / 255.0


def rotate_raster(data, center_lon, center_lat, out_h, out_w):
    """旋转栅格数据（支持 2D 和 3D）"""
    out_lons = np.linspace(-180, 180, out_w, endpoint=False)
    out_lats = np.linspace(90, -90, out_h, endpoint=False)
    out_lon_grid, out_lat_grid = np.meshgrid(out_lons, out_lats)

    lon_r = np.radians(out_lon_grid)
    lat_r = np.radians(out_lat_grid)
    clat = np.radians(center_lat)

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

    h, w = data.shape[:2]
    # DEM: lat 从 -90 到 90 (row 0 = 南极)
    # NE2: lat 从 90 到 -90 (row 0 = 北极, 标准图像格式)
    is_dem = (data.ndim == 2)

    if is_dem:
        col = (orig_lon + 180) / 360 * (w - 1)
        row = (orig_lat + 90) / 180 * (h - 1)
        rotated = map_coordinates(data, [row, col], order=1, mode='wrap')
    else:
        col = (orig_lon + 180) / 360 * (w - 1)
        row = (90 - orig_lat) / 180 * (h - 1)
        rotated = np.zeros((out_h, out_w, data.shape[2]), dtype=np.float32)
        for c in range(data.shape[2]):
            rotated[:, :, c] = map_coordinates(data[:, :, c], [row, col], order=1, mode='wrap')

    return rotated


def compute_hillshade(dem, azimuth=315, altitude=45, scale=3.0):
    """从 DEM 计算 hillshade"""
    dy, dx = np.gradient(dem, 1.0)
    dx *= scale
    dy *= scale

    az_rad = np.radians(azimuth)
    alt_rad = np.radians(altitude)

    slope = np.arctan(np.sqrt(dx**2 + dy**2))
    aspect = np.arctan2(-dx, dy)

    hillshade = (np.sin(alt_rad) * np.cos(slope) +
                 np.cos(alt_rad) * np.sin(slope) * np.cos(az_rad - aspect))

    hillshade = np.clip(hillshade, 0, 1)
    hillshade = 0.35 + 0.65 * hillshade
    return hillshade


def render_terrain(dem, ne2_rgb, hillshade):
    """合成最终图像：NE2颜色 + 高程覆盖 + hillshade + 海洋"""
    h, w = dem.shape
    rgb = np.zeros((h, w, 3), dtype=np.float32)

    ocean = dem < 0
    land = ~ocean

    # === 海洋：深蓝到黑 ===
    depth_norm = np.clip(-dem[ocean] / 10752, 0, 1)
    rgb[:, :, 0][ocean] = 0.02 + 0.06 * (1 - depth_norm)
    rgb[:, :, 1][ocean] = 0.04 + 0.10 * (1 - depth_norm)
    rgb[:, :, 2][ocean] = 0.15 + 0.20 * (1 - depth_norm)

    # === 陆地 ===
    # 基础颜色来自 Natural Earth 2（真实地表类型）
    land_color = ne2_rgb.copy()

    # 高海拔区域用高程色带渐变覆盖 NE2 颜色
    # 2000m 以下：100% NE2 颜色
    # 2000-3500m：NE2 渐变到高原棕
    # 3500-5000m：高原棕渐变到高山灰
    # 5000m+：高山灰渐变到雪白

    elev_land = dem.copy()
    elev_land[ocean] = 0

    # 高原棕色
    c_plateau = np.array([0.55, 0.42, 0.25])
    # 高山灰
    c_alpine = np.array([0.65, 0.60, 0.55])
    # 雪白
    c_snow = np.array([0.95, 0.95, 0.97])

    # 2000-3500m: 混合 NE2 → 高原棕
    mask1 = land & (dem >= 2000) & (dem < 3500)
    if mask1.any():
        t = ((dem[mask1] - 2000) / 1500)[:, np.newaxis]
        land_color[mask1] = land_color[mask1] * (1 - t) + c_plateau * t

    # 3500-5000m: 高原棕 → 高山灰
    mask2 = land & (dem >= 3500) & (dem < 5000)
    if mask2.any():
        t = ((dem[mask2] - 3500) / 1500)[:, np.newaxis]
        land_color[mask2] = c_plateau * (1 - t) + c_alpine * t

    # 5000m+: 高山灰 → 雪白
    mask3 = land & (dem >= 5000)
    if mask3.any():
        t = np.clip((dem[mask3] - 5000) / 2000, 0, 1)[:, np.newaxis]
        land_color[mask3] = c_alpine * (1 - t) + c_snow * t

    # 叠加 hillshade
    rgb[land] = land_color[land] * hillshade[land, np.newaxis]

    return np.clip(rgb, 0, 1)

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


def draw_rotated_features(ax, center_lon, center_lat):
    pc = ccrs.PlateCarree()
    for category, name, color, lw in [
        ("physical", "coastline", "#1a1a1a", 0.3),
        ("cultural", "admin_0_boundary_lines_land", "#444444", 0.2),
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


def make_map(proj_name, proj, center_lon, center_lat, center_key, dem, ne2):
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    ax = fig.add_subplot(1, 1, 1, projection=proj)
    ax.set_global()
    ax.set_facecolor('black')

    out_h, out_w = 5400, 10800

    print("    旋转 DEM + NE2...")
    rot_dem = rotate_raster(dem, center_lon, center_lat, out_h, out_w)
    rot_ne2 = rotate_raster(ne2, center_lon, center_lat, out_h, out_w)

    print("    计算 hillshade...")
    hillshade = compute_hillshade(rot_dem)

    print("    渲染地形...")
    rgb = render_terrain(rot_dem, rot_ne2, hillshade)

    ax.imshow(rgb, origin='upper', transform=ccrs.PlateCarree(),
              extent=[-180, 180, -90, 90], zorder=1, interpolation='bilinear')

    print("    绘制边界...")
    draw_rotated_features(ax, center_lon, center_lat)

    gl = ax.gridlines(linewidth=0.15, color='gray', alpha=0.3, linestyle='--', zorder=4)
    ax.plot(0, 0, 'r+', markersize=8, markeredgewidth=1,
            transform=ccrs.PlateCarree(), zorder=5)

    filename = f"map_v5_{center_key}_{proj_name}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=DPI, bbox_inches='tight', pad_inches=0.1,
                facecolor='black')
    plt.close(fig)
    print(f"  ✓ {filename}")


def main():
    print("=== v5: NE2 颜色 + DEM Hillshade ===")
    print(f"输出分辨率: {DPI}dpi (A1)")
    print("加载数据...")
    dem = load_etopo()
    ne2 = load_ne2()
    print(f"  DEM: {dem.shape}, NE2: {ne2.shape}")
    print()

    for m in MAPS_TO_GENERATE:
        proj = get_projection(m["proj"])
        print(f"[{m['center_key']} - {m['proj']}]")
        make_map(m["proj"], proj, m["lon"], m["lat"], m["center_key"], dem, ne2)
        print()

    print("完成！")


if __name__ == "__main__":
    main()
