#!/usr/bin/env python3
"""
生成以中国为中心的世界地形图（第四批，ASTER GDEM 3D浮雕版）。
两种投影 × 两种地形风格 × 两个中心点 = 8 张图。
通过球面坐标旋转，让中国中心点位于新赤道与本初子午线交点，
从而在标准投影下实现真正的x+y方向居中。
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from scipy.ndimage import map_coordinates
from matplotlib.image import imread
from pathlib import Path as PathLib
import cartopy
from shapely.geometry import LineString, MultiLineString
from cartopy.io.shapereader import Reader
import cartopy.io.shapereader as shpreader

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
DPI = 300
FIG_WIDTH = 7016 / DPI
FIG_HEIGHT = 4961 / DPI

CENTERS = {
    "china": {"lon": 103.0, "lat": 35.0, "label": "中国地理中心"},
    "beijing": {"lon": 116.4, "lat": 39.9, "label": "北京"},
}

PROJECTION_TYPES = ["robinson", "equalearth"]

STYLES = {
    "hypsometric": {
        "description": "彩色晕渲地形",
    },
    "shaded_relief": {
        "description": "浮雕阴影",
        "ocean_color": (0.10, 0.23, 0.36),
    },
}


# ---- Coordinate rotation ----
def rotate_coords(lon, lat, center_lon, center_lat):
    lon = np.asarray(lon, dtype=float)
    lat = np.asarray(lat, dtype=float)
    lon_rad = np.radians(lon)
    lat_rad = np.radians(lat)
    clon_rad = np.radians(center_lon)
    clat_rad = np.radians(center_lat)
    x = np.cos(lat_rad) * np.cos(lon_rad)
    y = np.cos(lat_rad) * np.sin(lon_rad)
    z = np.sin(lat_rad)
    x1 = x * np.cos(-clon_rad) - y * np.sin(-clon_rad)
    y1 = x * np.sin(-clon_rad) + y * np.cos(-clon_rad)
    z1 = z
    x2 = x1 * np.cos(clat_rad) + z1 * np.sin(clat_rad)
    y2 = y1
    z2 = -x1 * np.sin(clat_rad) + z1 * np.cos(clat_rad)
    new_lat = np.degrees(np.arcsin(np.clip(z2, -1, 1)))
    new_lon = np.degrees(np.arctan2(y2, x2))
    return new_lon, new_lat


def inverse_rotate_coords(new_lon, new_lat, center_lon, center_lat):
    new_lon = np.asarray(new_lon, dtype=float)
    new_lat = np.asarray(new_lat, dtype=float)
    nlon_rad = np.radians(new_lon)
    nlat_rad = np.radians(new_lat)
    clon_rad = np.radians(center_lon)
    clat_rad = np.radians(center_lat)
    x = np.cos(nlat_rad) * np.cos(nlon_rad)
    y = np.cos(nlat_rad) * np.sin(nlon_rad)
    z = np.sin(nlat_rad)
    x1 = x * np.cos(-clat_rad) + z * np.sin(-clat_rad)
    y1 = y
    z1 = -x * np.sin(-clat_rad) + z * np.cos(-clat_rad)
    x2 = x1 * np.cos(clon_rad) - y1 * np.sin(clon_rad)
    y2 = x1 * np.sin(clon_rad) + y1 * np.cos(clon_rad)
    z2 = z1
    orig_lat = np.degrees(np.arcsin(np.clip(z2, -1, 1)))
    orig_lon = np.degrees(np.arctan2(y2, x2))
    return orig_lon, orig_lat


def normalize_longitude(lon):
    lon = np.asarray(lon, dtype=float)
    return ((lon + 180) % 360) - 180


def split_line_at_meridian(line):
    coords = np.array(line.coords)
    if len(coords) < 2:
        return [line] if len(coords) > 1 else []
    lons = coords[:, 0]
    diffs = np.diff(lons)
    jump_indices = np.where(np.abs(diffs) > 180)[0]
    if len(jump_indices) == 0:
        return [line]
    segments = []
    start = 0
    for idx in jump_indices:
        seg_coords = coords[start:idx + 1]
        if len(seg_coords) > 1:
            segments.append(LineString(seg_coords))
        start = idx + 1
    seg_coords = coords[start:]
    if len(seg_coords) > 1:
        segments.append(LineString(seg_coords))
    return segments


def rotate_line_geometry(geom, center_lon, center_lat):
    if geom is None:
        return []
    if isinstance(geom, LineString):
        coords = np.array(geom.coords)
        if len(coords) < 2:
            return []
        new_lon, new_lat = rotate_coords(coords[:, 0], coords[:, 1], center_lon, center_lat)
        new_lon = normalize_longitude(new_lon)
        new_coords = list(zip(new_lon, new_lat))
        line = LineString(new_coords)
        return split_line_at_meridian(line)
    elif isinstance(geom, MultiLineString):
        all_lines = []
        for g in geom.geoms:
            all_lines.extend(rotate_line_geometry(g, center_lon, center_lat))
        return all_lines
    else:
        return []


# ---- Image rotation ----
def rotate_image(img, center_lon, center_lat):
    h, w = img.shape[:2]
    new_lon = np.linspace(-180, 180, w)
    new_lat = np.linspace(90, -90, h)
    new_lon_grid, new_lat_grid = np.meshgrid(new_lon, new_lat)
    orig_lon, orig_lat = inverse_rotate_coords(new_lon_grid, new_lat_grid, center_lon, center_lat)
    px = (orig_lon + 180) / 360 * (w - 1)
    py = (90 - orig_lat) / 180 * (h - 1)
    px = np.clip(px, 0, w - 1)
    py = np.clip(py, 0, h - 1)
    coords = np.array([py, px])
    if img.ndim == 3:
        result = np.zeros_like(img)
        for c in range(img.shape[2]):
            result[:, :, c] = map_coordinates(img[:, :, c], coords, order=1, mode='nearest')
    else:
        result = map_coordinates(img, coords, order=1, mode='nearest')
    return result


def replace_ocean(img, ocean_color=(0.10, 0.23, 0.36)):
    """Replace ASTER GDEM ocean pixels with a solid dark blue."""
    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    # ASTER GDEM ocean is uniformly blue-ish; land is green/brown/white.
    # This threshold catches ~69% of the globe (close to the 71% ocean ratio).
    is_ocean = (b > g + 0.05) & (b > r + 0.05) & (r < 0.45)
    result = img.copy()
    for c in range(3):
        result[:, :, c] = np.where(is_ocean, ocean_color[c], result[:, :, c])
    return result


# ---- Load base terrain image ----
base_img_path = os.path.join(OUTPUT_DIR, 'aster_gdem_10800x5400.jpg')
if not os.path.exists(base_img_path):
    print("Downloading ASTER GDEM terrain from NASA GIBS...")
    import urllib.request
    url = ("https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
           "?SERVICE=WMS&REQUEST=GetMap&LAYERS=ASTER_GDEM_Color_Shaded_Relief"
           "&VERSION=1.1.1&FORMAT=image/jpeg&SRS=EPSG:4326"
           "&BBOX=-180,-90,180,90&WIDTH=10800&HEIGHT=5400")
    urllib.request.urlretrieve(url, base_img_path)
    print("Download complete.")
base_img = imread(base_img_path)
if base_img.dtype == np.uint8:
    base_img = base_img.astype(np.float32) / 255.0
print(f"Base terrain image: {base_img.shape}")

# Pre-rotate terrain for each center
rotated_terrains = {}
for key, info in CENTERS.items():
    print(f"Pre-rotating terrain for {key}...")
    rotated_terrains[key] = rotate_image(base_img, info["lon"], info["lat"])

# ---- Feature caching ----
feature_cache = {}


def get_rotated_features(feature_name, category, name, center_lon, center_lat, resolution='110m'):
    cache_key = (feature_name, center_lon, center_lat, resolution)
    if cache_key not in feature_cache:
        reader = Reader(shpreader.natural_earth(resolution=resolution, category=category, name=name))
        geoms = []
        for record in reader.records():
            geoms.extend(rotate_line_geometry(record.geometry, center_lon, center_lat))
        feature_cache[cache_key] = geoms
    return feature_cache[cache_key]


def get_projection(proj_type):
    if proj_type == "robinson":
        return ccrs.Robinson()
    elif proj_type == "equalearth":
        return ccrs.EqualEarth()


def make_map(proj_name, proj, style_name, style_config, center_key, center_info):
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI)
    ax = fig.add_subplot(1, 1, 1, projection=proj)
    ax.set_global()

    clon, clat = center_info["lon"], center_info["lat"]
    terrain_img = rotated_terrains[center_key]

    if style_name == "shaded_relief":
        terrain_img = replace_ocean(terrain_img, style_config.get("ocean_color", (0.10, 0.23, 0.36)))

    ax.imshow(terrain_img, origin='upper', transform=ccrs.PlateCarree(), extent=[-180, 180, -90, 90])

    # Coastline
    for g in get_rotated_features('coastline', 'physical', 'coastline', clon, clat):
        ax.add_geometries([g], ccrs.PlateCarree(), facecolor='none', edgecolor='#333333', linewidth=0.5, zorder=3)

    # Borders
    for g in get_rotated_features('borders', 'cultural', 'admin_0_boundary_lines_land', clon, clat):
        ax.add_geometries([g], ccrs.PlateCarree(), facecolor='none', edgecolor='#666666', linewidth=0.3, zorder=3)

    # Rivers
    for g in get_rotated_features('rivers', 'physical', 'rivers_lake_centerlines', clon, clat):
        ax.add_geometries([g], ccrs.PlateCarree(), facecolor='none', edgecolor='#4a90d9', linewidth=0.3, zorder=2)

    # Gridlines
    gl = ax.gridlines(draw_labels=False, linewidth=0.3, color="gray", alpha=0.5, linestyle="--")
    gl.xlocator = plt.FixedLocator(range(-180, 181, 30))
    gl.ylocator = plt.FixedLocator(range(-90, 91, 30))

    # Center mark
    ax.plot(0, 0, 'r+', markersize=12, markeredgewidth=2, transform=ccrs.PlateCarree(), zorder=5)

    plt.tight_layout(pad=0.5)
    filename = f"map_v4_{center_key}_{proj_name}_{style_name}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=DPI, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    print(f"  ✓ {filename}")


def main():
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"分辨率: {DPI}dpi (A1)")
    print()
    total = 0
    for center_key, center_info in CENTERS.items():
        print(f"=== {center_info['label']} ({center_info['lon']}°E, {center_info['lat']}°N) ===")
        for proj_name in PROJECTION_TYPES:
            proj = get_projection(proj_name)
            print(f"  [{proj_name}]")
            for style_name, style_config in STYLES.items():
                make_map(proj_name, proj, style_name, style_config, center_key, center_info)
                total += 1
        print()
    print(f"完成！共生成 {total} 张地图。")


if __name__ == "__main__":
    main()
