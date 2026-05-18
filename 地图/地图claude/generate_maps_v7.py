#!/usr/bin/env python3
"""
v7: 高精度直出 + 修正旋转 + 修正颜色。
- 绕过 matplotlib，直接用 pyproj 投影逆变换 + PIL 输出
- 目标分辨率：50000×25000
- 修正 bearing 旋转（绕 X 轴/视线轴）
- 颜色用曲线调整而非像素分类
"""

import os
import numpy as np
import netCDF4 as nc
from scipy.ndimage import map_coordinates
from PIL import Image
from pyproj import Transformer, CRS

Image.MAX_IMAGE_PIXELS = None

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
ETOPO_PATH = os.path.join(OUTPUT_DIR, "ETOPO_2022_v1_60s.nc")
NE2_HR_PATH = os.path.join(OUTPUT_DIR, "NE2_HR_raster", "NE2_HR_LC_SR_W_DR.tif")

OUT_W = 50000
OUT_H = 25000

MAPS_TO_GENERATE = [
    {"center_key": "beijing", "lon": 116.4, "lat": 39.9, "proj": "robin"},
    {"center_key": "china", "lon": 103.0, "lat": 35.0, "proj": "eqearth"},
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
    """用色彩曲线调整，保持空间连续性。
    森林（暗绿区域）→ 墨绿 #004D33
    草原（亮绿区域）→ 浅黄绿
    沙漠保持不变
    """
    r, g, b = ne2_rgb[:, :, 0], ne2_rgb[:, :, 1], ne2_rgb[:, :, 2]
    enhanced = ne2_rgb.copy()

    # 计算"绿色程度"（连续值，不是二值分类）
    greenness = np.clip((g - np.maximum(r, b)) / (g + 0.01), 0, 1)
    # 计算亮度
    brightness = (r + g + b) / 3.0

    # 森林权重：绿色程度高 且 亮度低
    forest_w = np.clip(greenness * 2, 0, 1) * np.clip(1.0 - brightness * 2.5, 0, 1)
    # 草原权重：绿色程度中等 且 亮度高
    grass_w = np.clip(greenness * 1.5, 0, 1) * np.clip(brightness * 2 - 0.5, 0, 1)

    # 墨绿目标色 #004D33 = (0, 0.30, 0.20)
    forest_color = np.array([0.0, 0.30, 0.20])
    # 浅黄绿目标色
    grass_color = np.array([0.55, 0.65, 0.30])

    for ch in range(3):
        enhanced[:, :, ch] = (
            ne2_rgb[:, :, ch] * (1 - forest_w - grass_w) +
            forest_color[ch] * forest_w +
            grass_color[ch] * grass_w
        )

    return np.clip(enhanced, 0, 1)

def rotate_globe(lon, lat, center_lon, center_lat, bearing=0):
    """正向旋转：将地理坐标旋转使 center 在中心，bearing 绕视线轴旋转。
    返回旋转后的 (lon, lat)。"""
    lon_r = np.radians(np.asarray(lon, dtype=np.float64))
    lat_r = np.radians(np.asarray(lat, dtype=np.float64))
    clon = np.radians(center_lon)
    clat = np.radians(center_lat)

    # 笛卡尔
    x = np.cos(lat_r) * np.cos(lon_r - clon)
    y = np.cos(lat_r) * np.sin(lon_r - clon)
    z = np.sin(lat_r)

    # 绕 Y 轴旋转 clat（把中心纬度移到赤道）
    cos_a = np.cos(clat)
    sin_a = np.sin(clat)
    x1 = x * cos_a + z * sin_a
    z1 = -x * sin_a + z * cos_a
    y1 = y

    # 绕 X 轴旋转 bearing（视线轴旋转，中心点不动）
    if bearing != 0:
        br = np.radians(bearing)
        cb = np.cos(br)
        sb = np.sin(br)
        y2 = y1 * cb - z1 * sb
        z2 = y1 * sb + z1 * cb
        y1, z1 = y2, z2

    new_lat = np.degrees(np.arcsin(np.clip(z1, -1, 1)))
    new_lon = np.degrees(np.arctan2(y1, x1))
    return new_lon, new_lat


def inverse_rotate(out_lon, out_lat, center_lon, center_lat, bearing=0):
    """逆向旋转：从输出坐标找原始地理坐标。"""
    lon_r = np.radians(np.asarray(out_lon, dtype=np.float64))
    lat_r = np.radians(np.asarray(out_lat, dtype=np.float64))
    clat = np.radians(center_lat)

    x = np.cos(lat_r) * np.cos(lon_r)
    y = np.cos(lat_r) * np.sin(lon_r)
    z = np.sin(lat_r)

    # 反向绕 X 轴旋转 -bearing
    if bearing != 0:
        br = np.radians(-bearing)
        cb = np.cos(br)
        sb = np.sin(br)
        y2 = y * cb - z * sb
        z2 = y * sb + z * cb
        y, z = y2, z2

    # 反向绕 Y 轴旋转 -clat
    cos_a = np.cos(-clat)
    sin_a = np.sin(-clat)
    x_orig = x * cos_a + z * sin_a
    z_orig = -x * sin_a + z * cos_a

    orig_lat = np.degrees(np.arcsin(np.clip(z_orig, -1, 1)))
    orig_lon = np.degrees(np.arctan2(y, x_orig)) + center_lon
    orig_lon = (orig_lon + 180) % 360 - 180
    return orig_lon, orig_lat


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
    return 0.3 + 0.7 * np.clip(hs, 0, 1)


def sample_data(data, orig_lon, orig_lat):
    """从原始数据中采样（支持 2D DEM 和 3D RGB）"""
    h, w = data.shape[:2]
    is_dem = (data.ndim == 2)

    if is_dem:
        col = (orig_lon + 180) / 360 * (w - 1)
        row = (orig_lat + 90) / 180 * (h - 1)
        return map_coordinates(data, [row, col], order=1, mode='wrap')
    else:
        col = (orig_lon + 180) / 360 * (w - 1)
        row = (90 - orig_lat) / 180 * (h - 1)
        out = np.zeros(orig_lon.shape + (data.shape[2],), dtype=np.float32)
        for c in range(data.shape[2]):
            out[:, :, c] = map_coordinates(data[:, :, c], [row, col], order=1, mode='wrap')
        return out

def render_terrain(dem, ne2_rgb, hillshade):
    """合成地形图像"""
    h, w = dem.shape
    rgb = np.zeros((h, w, 3), dtype=np.float32)

    ocean = dem < 0
    land = ~ocean

    # 海洋
    depth_norm = np.clip(-dem[ocean] / 10752, 0, 1)
    rgb[:, :, 0][ocean] = 0.02 + 0.06 * (1 - depth_norm)
    rgb[:, :, 1][ocean] = 0.04 + 0.10 * (1 - depth_norm)
    rgb[:, :, 2][ocean] = 0.15 + 0.20 * (1 - depth_norm)

    # 陆地
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
    return np.clip((rgb * 255).astype(np.uint8), 0, 255)


def get_projection_bounds(proj_name):
    """获取投影的 x/y 范围"""
    if proj_name == "robin":
        crs = CRS.from_proj4("+proj=robin +lon_0=0 +datum=WGS84")
    elif proj_name == "eqearth":
        crs = CRS.from_proj4("+proj=eqearth +lon_0=0 +datum=WGS84")

    t = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    # 投影边界
    x_max, _ = t.transform(180, 0)
    _, y_max = t.transform(0, 90)
    return crs, x_max, y_max


def make_map(proj_name, center_lon, center_lat, center_key, dem, ne2, bearing=0):
    print(f"    获取投影范围...")
    crs, x_max, y_max = get_projection_bounds(proj_name)
    t_inv = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

    aspect = x_max / y_max
    img_w = OUT_W
    img_h = int(OUT_W / aspect)
    if img_h > OUT_H:
        img_h = OUT_H
        img_w = int(OUT_H * aspect)

    print(f"    输出尺寸: {img_w}x{img_h}")

    # 分块处理，每块 500 行
    CHUNK = 500
    xs = np.linspace(-x_max, x_max, img_w)
    ys = np.linspace(y_max, -y_max, img_h)

    # 创建输出数组（uint8 节省内存）
    output = np.zeros((img_h, img_w, 3), dtype=np.uint8)

    n_chunks = (img_h + CHUNK - 1) // CHUNK
    for ci in range(n_chunks):
        r0 = ci * CHUNK
        r1 = min(r0 + CHUNK, img_h)
        chunk_ys = ys[r0:r1]

        xgrid, ygrid = np.meshgrid(xs, chunk_ys)

        # 逆投影
        rot_lon, rot_lat = t_inv.transform(xgrid.ravel(), ygrid.ravel())
        rot_lon = rot_lon.reshape(r1 - r0, img_w)
        rot_lat = rot_lat.reshape(r1 - r0, img_w)

        valid = np.isfinite(rot_lon) & np.isfinite(rot_lat)
        rot_lon[~valid] = 0
        rot_lat[~valid] = 0

        # 逆旋转
        orig_lon, orig_lat = inverse_rotate(rot_lon, rot_lat, center_lon, center_lat, bearing)

        # 采样
        chunk_dem = sample_data(dem, orig_lon, orig_lat)
        chunk_ne2 = sample_data(ne2, orig_lon, orig_lat)

        # hillshade + 渲染
        hs = compute_hillshade(chunk_dem)
        chunk_rgb = render_terrain(chunk_dem, chunk_ne2, hs)
        chunk_rgb[~valid] = 0

        output[r0:r1] = chunk_rgb

        if (ci + 1) % 10 == 0 or ci == n_chunks - 1:
            print(f"      chunk {ci+1}/{n_chunks}")

    rot_suffix = {0: "", 90: "_east_up", -90: "_west_up"}[bearing]
    filename = f"map_v7_{center_key}_{proj_name}{rot_suffix}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)

    print(f"    保存 {filename}...")
    img = Image.fromarray(output, 'RGB')
    img.save(filepath, optimize=True)
    fsize = os.path.getsize(filepath) / 1024 / 1024
    print(f"  ✓ {filename} ({img_w}x{img_h}, {fsize:.1f}MB)")


def main():
    print("=== v7: 高精度直出 ===")
    print(f"目标分辨率: {OUT_W}x{OUT_H}")
    print("加载数据...")
    dem = load_etopo()
    ne2_raw = load_ne2()
    print(f"  DEM: {dem.shape}, NE2: {ne2_raw.shape}")

    print("增强颜色...")
    ne2 = enhance_colors(ne2_raw)
    print()

    for m in MAPS_TO_GENERATE:
        for bearing in [0, 90, -90]:
            rot_label = {0: "北在上", 90: "东在上", -90: "西在上"}[bearing]
            print(f"[{m['center_key']} - {m['proj']} - {rot_label}]")
            make_map(m["proj"], m["lon"], m["lat"], m["center_key"], dem, ne2, bearing)
            print()

    print("完成！")


if __name__ == "__main__":
    main()
