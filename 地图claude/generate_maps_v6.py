#!/usr/bin/env python3
"""
v6: 高分辨率 + 森林/草原颜色增强 + 旋转版本。
- NE2 高分辨率 (21600x10800) + DEM 全分辨率 (21600x10800)
- 森林：深绿（发黑），草原：浅黄绿
- 输出：2 张正常 + 4 张旋转 90° = 6 张
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import netCDF4 as nc
from scipy.ndimage import map_coordinates
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
ETOPO_PATH = os.path.join(OUTPUT_DIR, "ETOPO_2022_v1_60s.nc")
NE2_HR_PATH = os.path.join(OUTPUT_DIR, "NE2_HR_raster", "NE2_HR_LC_SR_W_DR.tif")

DPI = 300
FIG_WIDTH = 7016 / DPI
FIG_HEIGHT = 4961 / DPI

OUT_H = 10800
OUT_W = 21600

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
    img = Image.open(NE2_HR_PATH)
    return np.array(img).astype(np.float32) / 255.0


def enhance_colors(ne2_rgb):
    """增强森林/草原颜色区分：森林→深黑绿，草原→浅黄绿"""
    r, g, b = ne2_rgb[:, :, 0], ne2_rgb[:, :, 1], ne2_rgb[:, :, 2]

    # 检测绿色区域（植被）
    is_green = (g > r + 0.02) & (g > b + 0.02) & (g > 0.15)

    # 森林：绿色较深的区域
    is_forest = is_green & (g < 0.55) & (r < 0.35)
    # 草原：绿色较浅的区域
    is_grassland = is_green & ((g >= 0.55) | (r >= 0.35))

    enhanced = ne2_rgb.copy()

    # 森林 → 墨绿（极深的绿，几乎发黑）
    if is_forest.any():
        enhanced[:, :, 0][is_forest] = 0.03
        enhanced[:, :, 1][is_forest] = 0.12
        enhanced[:, :, 2][is_forest] = 0.03

    # 草原 → 浅黄绿（明亮，带黄调）
    if is_grassland.any():
        enhanced[:, :, 0][is_grassland] = 0.55
        enhanced[:, :, 1][is_grassland] = 0.62
        enhanced[:, :, 2][is_grassland] = 0.25

    return np.clip(enhanced, 0, 1)

def rotate_raster(data, center_lon, center_lat, out_h, out_w, bearing=0):
    """旋转栅格。bearing: 绕视线轴旋转角度（90=东在上，-90=西在上）"""
    out_lons = np.linspace(-180, 180, out_w, endpoint=False)
    out_lats = np.linspace(90, -90, out_h, endpoint=False)
    out_lon_grid, out_lat_grid = np.meshgrid(out_lons, out_lats)

    lon_r = np.radians(out_lon_grid)
    lat_r = np.radians(out_lat_grid)
    clat = np.radians(center_lat)
    bearing_r = np.radians(bearing)

    # 输出坐标转笛卡尔
    x = np.cos(lat_r) * np.cos(lon_r)
    y = np.cos(lat_r) * np.sin(lon_r)
    z = np.sin(lat_r)

    # 先反向 bearing 旋转（绕 Z 轴）
    if bearing != 0:
        cb = np.cos(-bearing_r)
        sb = np.sin(-bearing_r)
        x2 = x * cb - y * sb
        y2 = x * sb + y * cb
        x, y = x2, y2

    # 反向纬度旋转（绕 Y 轴）
    cos_a = np.cos(-clat)
    sin_a = np.sin(-clat)
    x_orig = x * cos_a + z * sin_a
    z_orig = -x * sin_a + z * cos_a

    orig_lat = np.degrees(np.arcsin(np.clip(z_orig, -1, 1)))
    orig_lon = np.degrees(np.arctan2(y, x_orig)) + center_lon
    orig_lon = (orig_lon + 180) % 360 - 180

    h, w = data.shape[:2]
    is_dem = (data.ndim == 2)

    if is_dem:
        col = (orig_lon + 180) / 360 * (w - 1)
        row = (orig_lat + 90) / 180 * (h - 1)
        return map_coordinates(data, [row, col], order=1, mode='wrap')
    else:
        col = (orig_lon + 180) / 360 * (w - 1)
        row = (90 - orig_lat) / 180 * (h - 1)
        rotated = np.zeros((out_h, out_w, data.shape[2]), dtype=np.float32)
        for c in range(data.shape[2]):
            rotated[:, :, c] = map_coordinates(data[:, :, c], [row, col], order=1, mode='wrap')
        return rotated


def compute_hillshade(dem, azimuth=315, altitude=45, scale=2.5):
    dy, dx = np.gradient(dem, 1.0)
    dx *= scale
    dy *= scale
    az_rad = np.radians(azimuth)
    alt_rad = np.radians(altitude)
    slope = np.arctan(np.sqrt(dx**2 + dy**2))
    aspect = np.arctan2(-dx, dy)
    hs = (np.sin(alt_rad) * np.cos(slope) +
          np.cos(alt_rad) * np.sin(slope) * np.cos(az_rad - aspect))
    hs = np.clip(hs, 0, 1)
    return 0.3 + 0.7 * hs


def render_terrain(dem, ne2_rgb, hillshade):
    h, w = dem.shape
    rgb = np.zeros((h, w, 3), dtype=np.float32)

    ocean = dem < 0
    land = ~ocean

    # 海洋：深蓝到黑
    depth_norm = np.clip(-dem[ocean] / 10752, 0, 1)
    rgb[:, :, 0][ocean] = 0.02 + 0.06 * (1 - depth_norm)
    rgb[:, :, 1][ocean] = 0.04 + 0.10 * (1 - depth_norm)
    rgb[:, :, 2][ocean] = 0.15 + 0.20 * (1 - depth_norm)

    # 陆地颜色
    land_color = ne2_rgb.copy()

    c_plateau = np.array([0.55, 0.42, 0.25])
    c_alpine = np.array([0.65, 0.60, 0.55])
    c_snow = np.array([0.95, 0.95, 0.97])

    mask1 = land & (dem >= 2000) & (dem < 3500)
    if mask1.any():
        t = ((dem[mask1] - 2000) / 1500)[:, np.newaxis]
        land_color[mask1] = land_color[mask1] * (1 - t) + c_plateau * t

    mask2 = land & (dem >= 3500) & (dem < 5000)
    if mask2.any():
        t = ((dem[mask2] - 3500) / 1500)[:, np.newaxis]
        land_color[mask2] = c_plateau * (1 - t) + c_alpine * t

    mask3 = land & (dem >= 5000)
    if mask3.any():
        t = np.clip((dem[mask3] - 5000) / 2000, 0, 1)[:, np.newaxis]
        land_color[mask3] = c_alpine * (1 - t) + c_snow * t

    rgb[land] = land_color[land] * hillshade[land, np.newaxis]
    return np.clip(rgb, 0, 1)

def rotate_point(lon, lat, center_lon, center_lat, bearing=0):
    lon_r = np.radians(np.asarray(lon, dtype=float))
    lat_r = np.radians(np.asarray(lat, dtype=float))
    clon = np.radians(center_lon)
    clat = np.radians(center_lat)
    x = np.cos(lat_r) * np.cos(lon_r - clon)
    y = np.cos(lat_r) * np.sin(lon_r - clon)
    z = np.sin(lat_r)
    # 绕 Y 轴旋转（纬度居中）
    cos_a = np.cos(clat)
    sin_a = np.sin(clat)
    x_new = x * cos_a + z * sin_a
    z_new = -x * sin_a + z * cos_a
    # 绕 Z 轴旋转（bearing）
    if bearing != 0:
        br = np.radians(bearing)
        cb = np.cos(br)
        sb = np.sin(br)
        x2 = x_new * cb - y * sb
        y2 = x_new * sb + y * cb
        x_new, y = x2, y2
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


def draw_rotated_features(ax, center_lon, center_lat, bearing=0):
    pc = ccrs.PlateCarree()
    features = [
        ("physical", "coastline", "#1a1a1a", 0.25),
        ("cultural", "admin_0_boundary_lines_land", "#444444", 0.15),
        ("physical", "rivers_lake_centerlines", "#1565C0", 0.2),
    ]
    for category, name, color, lw in features:
        shp_path = shpreader.natural_earth(resolution='110m', category=category, name=name)
        reader = shpreader.Reader(shp_path)
        for geom in reader.geometries():
            lines = list(geom.geoms) if hasattr(geom, 'geoms') else [geom]
            for line in lines:
                coords = np.array(line.coords)
                rot_lon, rot_lat = rotate_point(coords[:, 0], coords[:, 1],
                                                center_lon, center_lat, bearing)
                rotated = np.column_stack([rot_lon, rot_lat])
                for seg in split_line_at_dateline(rotated):
                    ax.plot(seg[:, 0], seg[:, 1], color=color, linewidth=lw,
                            transform=pc, zorder=3)

    # 湖泊（面状要素）
    shp_path = shpreader.natural_earth(resolution='110m', category='physical', name='lakes')
    reader = shpreader.Reader(shp_path)
    for geom in reader.geometries():
        polys = list(geom.geoms) if hasattr(geom, 'geoms') else [geom]
        for poly in polys:
            coords = np.array(poly.exterior.coords)
            rot_lon, rot_lat = rotate_point(coords[:, 0], coords[:, 1],
                                            center_lon, center_lat, bearing)
            rotated = np.column_stack([rot_lon, rot_lat])
            for seg in split_line_at_dateline(rotated):
                ax.fill(seg[:, 0], seg[:, 1], facecolor='#1565C0', edgecolor='none',
                        transform=pc, zorder=3, alpha=0.8)


def get_projection(proj_type):
    if proj_type == "robinson":
        return ccrs.Robinson(central_longitude=0)
    elif proj_type == "equalearth":
        return ccrs.EqualEarth(central_longitude=0)


def make_map(proj_name, proj, center_lon, center_lat, center_key, dem, ne2, bearing=0):
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    ax = fig.add_subplot(1, 1, 1, projection=proj)
    ax.set_global()
    ax.set_facecolor('black')

    print("    旋转数据...")
    rot_dem = rotate_raster(dem, center_lon, center_lat, OUT_H, OUT_W, bearing)
    rot_ne2 = rotate_raster(ne2, center_lon, center_lat, OUT_H, OUT_W, bearing)

    print("    hillshade + 渲染...")
    hillshade = compute_hillshade(rot_dem)
    rgb = render_terrain(rot_dem, rot_ne2, hillshade)

    ax.imshow(rgb, origin='upper', transform=ccrs.PlateCarree(),
              extent=[-180, 180, -90, 90], zorder=1, interpolation='bilinear')

    print("    绘制要素...")
    draw_rotated_features(ax, center_lon, center_lat, bearing)

    gl = ax.gridlines(linewidth=0.12, color='gray', alpha=0.25, linestyle='--', zorder=4)
    ax.plot(0, 0, 'r+', markersize=6, markeredgewidth=0.8,
            transform=ccrs.PlateCarree(), zorder=5)

    rot_suffix = {0: "", 90: "_east_up", -90: "_west_up"}[bearing]
    filename = f"map_v6_{center_key}_{proj_name}{rot_suffix}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)

    fig.savefig(filepath, dpi=DPI, bbox_inches='tight', pad_inches=0.1,
                facecolor='black')
    plt.close(fig)
    print(f"  ✓ {filename}")


def main():
    print("=== v6: 高分辨率 + 颜色增强 + 旋转 ===")
    print(f"内部分辨率: {OUT_W}x{OUT_H} ({OUT_W/360:.0f} px/度)")
    print("加载数据...")
    dem = load_etopo()
    ne2_raw = load_ne2()
    print(f"  DEM: {dem.shape}, NE2: {ne2_raw.shape}")

    print("增强颜色...")
    ne2 = enhance_colors(ne2_raw)
    print()

    for m in MAPS_TO_GENERATE:
        proj = get_projection(m["proj"])
        for bearing in [0, 90, -90]:
            rot_label = {0: "正常(北在上)", 90: "东在上", -90: "西在上"}[bearing]
            print(f"[{m['center_key']} - {m['proj']} - {rot_label}]")
            make_map(m["proj"], proj, m["lon"], m["lat"], m["center_key"], dem, ne2, bearing)
        print()

    print("完成！")


if __name__ == "__main__":
    main()
