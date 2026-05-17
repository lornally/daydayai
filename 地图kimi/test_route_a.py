#!/usr/bin/env python3
"""
路线 A：基于 ASTER GDEM Color Index 反推高程 + 自计算山体阴影 + 自定义 colormap
- 从 Color Index 颜色估算高程
- numpy 计算 hillshade
- 自定义高程分层设色
"""

import numpy as np
from matplotlib.image import imread
import matplotlib.pyplot as plt
from matplotlib.colors import rgb_to_hsv, hsv_to_rgb

# Load Color Index (RGBA, transparent where ocean)
img = imread('aster_gdem_color_index.png')
if img.dtype == np.uint8:
    img = img.astype(np.float32) / 255.0

rgb = img[:,:,:3]
alpha = img[:,:,3]
land_mask = alpha > 0.1

# ---- Estimate elevation from color ----
# Convert to HSV for easier analysis
hsv = rgb_to_hsv(rgb)
h = hsv[:,:,0]  # Hue: 0=red, 0.33=green, 0.66=blue
s = hsv[:,:,1]  # Saturation
v = hsv[:,:,2]  # Value/brightness

# ASTER GDEM Color Index approximate elevation mapping:
# - Deep green (H~0.33, S~1.0, V~0.3-0.5) → 0-200m
# - Bright green (H~0.30, S~1.0, V~0.5-0.7) → 200-500m
# - Yellow-green (H~0.20, S~1.0, V~0.6-0.8) → 500-1000m
# - Yellow (H~0.15, S~1.0, V~0.7-0.9) → 1000-2000m
# - Orange (H~0.08, S~1.0, V~0.7-0.9) → 2000-4000m
# - Brown/Red (H~0.03, S~0.8, V~0.5-0.7) → 4000-6000m
# - White (S<0.2, V>0.8) → >6000m or snow

# Build elevation estimate (0 to 9000m)
elev = np.zeros_like(h)

# White / very light = highest (snow caps)
snow_mask = (s < 0.25) & (v > 0.7) & land_mask
elev[snow_mask] = 8000

# Brown / red = high mountains
brown_mask = (h < 0.06) & (s > 0.4) & (v < 0.75) & land_mask & (~snow_mask)
elev[brown_mask] = 5000 + 2000 * v[brown_mask]

# Orange = high
orange_mask = (h < 0.12) & (h >= 0.06) & (s > 0.5) & land_mask & (~snow_mask) & (~brown_mask)
elev[orange_mask] = 3000 + 2000 * (1 - h[orange_mask] / 0.12)

# Yellow = medium-high
yellow_mask = (h < 0.18) & (h >= 0.12) & (s > 0.5) & land_mask & (~snow_mask)
elev[yellow_mask] = 1500 + 1500 * (1 - (h[yellow_mask] - 0.12) / 0.06)

# Yellow-green = medium
yg_mask = (h < 0.27) & (h >= 0.18) & (s > 0.3) & land_mask & (~snow_mask)
elev[yg_mask] = 500 + 1000 * (1 - (h[yg_mask] - 0.18) / 0.09)

# Green = low
green_mask = (h >= 0.27) & (s > 0.2) & land_mask & (~snow_mask)
elev[green_mask] = 100 + 400 * (1 - (h[green_mask] - 0.27) / 0.15)

# Fill any remaining land pixels with interpolation from neighbors
from scipy.ndimage import gaussian_filter

# Smooth slightly to reduce color quantization artifacts
elev_smooth = gaussian_filter(elev, sigma=1.0)
# But keep original where we had values
elev = np.where(elev > 0, elev, elev_smooth)
elev = np.maximum(elev, 0)

print(f"Elevation range: {elev[land_mask].min():.0f} - {elev[land_mask].max():.0f}m")

# ---- Calculate hillshade ----
def calculate_hillshade(elevation, azimuth=315, altitude=45, cell_size=1.0):
    """Calculate hillshade from elevation array."""
    # Compute gradients
    dx, dy = np.gradient(elevation, cell_size)
    
    # Slope and aspect
    slope = np.arctan(np.sqrt(dx**2 + dy**2))
    aspect = np.arctan2(-dy, dx)  # Negative dy for geographic convention
    
    # Convert azimuth and altitude to radians
    azimuth_rad = np.radians(azimuth)
    altitude_rad = np.radians(altitude)
    
    # Hillshade formula
    shaded = (np.sin(altitude_rad) * np.sin(slope) + 
              np.cos(altitude_rad) * np.cos(slope) * 
              np.cos(azimuth_rad - aspect))
    
    # Normalize to 0-1
    shaded = (shaded + 1) / 2
    return np.clip(shaded, 0, 1)

# Calculate hillshade (use smaller cell size for steeper gradients = more dramatic shadows)
hillshade = calculate_hillshade(elev, azimuth=315, altitude=35, cell_size=0.5)

# ---- Custom colormap based on elevation ----
# User requirements:
# - Low elevation (plains): some base color
# - Medium: transition
# - Desert areas: yellow (but we can't distinguish desert from plain by elevation alone)
# - High mountains: brown-white
# - Snow: white

# For pure elevation-based coloring (Route A), we use a hypsometric tint:
def elev_to_color(e):
    """Map elevation in meters to RGB."""
    colors = np.array([
        [ 30, 100,  40],  # 0m: dark green (low plains)
        [ 60, 140,  60],  # 200m: green
        [120, 170,  80],  # 500m: yellow-green
        [180, 190, 100],  # 1000m: pale yellow-green
        [210, 180, 120],  # 1500m: tan
        [200, 160, 100],  # 2000m: light brown
        [180, 140,  90],  # 3000m: brown
        [160, 120,  80],  # 4000m: dark brown
        [180, 160, 140],  # 5000m: grey-brown
        [220, 210, 200],  # 6000m: light grey
        [250, 250, 250],  # 7000m+: white
    ], dtype=np.float32) / 255.0
    
    levels = np.array([0, 200, 500, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 7000])
    
    # Interpolate
    result = np.zeros((e.shape[0], e.shape[1], 3), dtype=np.float32)
    for c in range(3):
        result[:,:,c] = np.interp(e, levels, colors[:,c])
    return result

base_color = elev_to_color(elev)

# Apply hillshade (multiply mode with some ambient)
ambient = 0.3
hillshade_3d = ambient + (1 - ambient) * hillshade
for c in range(3):
    base_color[:,:,c] *= hillshade_3d

# Ocean
ocean_color = np.array([15, 30, 50], dtype=np.float32) / 255.0
for c in range(3):
    base_color[:,:,c] = np.where(land_mask, base_color[:,:,c], ocean_color[c])

base_color = np.clip(base_color, 0, 1)

# Save
plt.imsave('test_route_a_base.png', base_color)
print("Saved test_route_a_base.png")

# China crop
x1 = int((73 + 180) / 360 * 10800)
x2 = int((136 + 180) / 360 * 10800)
y1 = int((90 - 54) / 180 * 5400)
y2 = int((90 - 18) / 180 * 5400)
china_crop = base_color[y1:y2, x1:x2]
plt.imsave('test_route_a_china_crop.png', china_crop)
print(f"Saved China crop: {china_crop.shape}")
