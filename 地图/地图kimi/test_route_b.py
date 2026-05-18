#!/usr/bin/env python3
"""
路线 B：ASTER GDEM + MODIS Land Cover 叠加
- MODIS Land Cover 提供地表类型分类
- ASTER GDEM Greyscale 提供山体阴影/明暗
- 自定义颜色：沙漠黄、森林绿、草原浅黄绿、雪山白
"""

import numpy as np
from matplotlib.image import imread
import matplotlib.pyplot as plt

# Load data
lc = imread('modis_landcover_global.png')  # RGBA
grey = imread('aster_gdem_greyscale.jpg')  # RGB greyscale

# Convert to 0-1 float
if lc.dtype == np.uint8:
    lc = lc.astype(np.float32) / 255.0
if grey.dtype == np.uint8:
    grey = grey.astype(np.float32) / 255.0

rgb = lc[:,:,:3]
alpha = lc[:,:,3] if lc.shape[2] == 4 else np.ones_like(lc[:,:,0])

# ASTER greyscale is RGB, take luminance
grey_val = 0.299*grey[:,:,0] + 0.587*grey[:,:,1] + 0.114*grey[:,:,2]

r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]

# ---- Fast classification by color thresholds ----
# Initialize with ocean color
result = np.zeros_like(rgb)
ocean_color = np.array([26, 58, 92], dtype=np.float32) / 255.0
result[:,:,:] = ocean_color

# Color matching with tolerance
def match_color(target_r, target_g, target_b, tol=0.08):
    return (np.abs(r - target_r) < tol) & (np.abs(g - target_g) < tol) & (np.abs(b - target_b) < tol)

# Define masks and target colors
masks_targets = [
    # (mask, [R,G,B], description)
    (match_color(1.0, 1.0, 1.0, 0.05), [1.0, 1.0, 1.0], "snow"),          # Snow/Ice
    (match_color(0.94, 0.725, 0.40, 0.08), [0.83, 0.65, 0.45], "desert"),   # Desert/Barren
    (match_color(0.75, 0.75, 0.74, 0.05), [0.71, 0.63, 0.55], "rock"),      # Rock/Tibet (brown-white)
    (match_color(1.0, 0.835, 0.0, 0.08), [0.78, 0.72, 0.45], "cropland"),   # Cropland
    (match_color(0.96, 0.87, 0.70, 0.06), [0.74, 0.78, 0.51], "savanna"),   # Savanna
    (match_color(0.855, 0.92, 0.615, 0.06), [0.72, 0.76, 0.47], "grass1"),  # Grassland
    (match_color(0.98, 0.937, 0.45, 0.08), [0.73, 0.77, 0.49], "grass2"),   # Grassland
    (match_color(0.192, 0.80, 0.192, 0.08), [0.18, 0.47, 0.18], "forest1"), # Forest bright
    (match_color(0.553, 0.73, 0.553, 0.06), [0.22, 0.51, 0.22], "forest2"), # Forest grey-green
    (match_color(0.129, 0.541, 0.129, 0.06), [0.14, 0.38, 0.14], "forest3"), # Forest dark
    (match_color(0.588, 0.98, 0.588, 0.08), [0.24, 0.55, 0.24], "forest4"), # Forest light
    (match_color(0.278, 0.514, 0.71, 0.06), [0.24, 0.47, 0.63], "water"),   # Inland water
    (match_color(0.60, 0.576, 0.337, 0.06), [0.78, 0.67, 0.47], "barren"),  # Barren
    (match_color(1.0, 0.0, 0.0, 0.05), [0.63, 0.24, 0.24], "urban"),        # Urban
    (match_color(0.596, 0.80, 0.192, 0.08), [0.28, 0.51, 0.20], "forest5"), # Forest edge
    (match_color(0.73, 0.553, 0.553, 0.06), [0.75, 0.67, 0.51], "sparse"),  # Sparse
    (match_color(0.392, 0.392, 0.392, 0.05), [0.31, 0.31, 0.31], "urban2"), # Urban grey
]

for mask, color, _ in masks_targets:
    mask = mask & (alpha > 0.1)
    for c in range(3):
        result[:,:,c] = np.where(mask, color[c], result[:,:,c])

# ---- Apply hillshade modulation ----
# Only modulate land (non-ocean) pixels
ocean_mask = (np.abs(r - 0.525) < 0.08) & (np.abs(g - 0.792) < 0.08) & (np.abs(b - 0.89) < 0.08)
land_mask = (~ocean_mask) & (alpha > 0.1)

modulation = 0.4 + 0.6 * grey_val
for c in range(3):
    channel = result[:,:,c].copy()
    channel[land_mask] *= modulation[land_mask]
    result[:,:,c] = channel

result = np.clip(result, 0, 1)

# Save full
plt.imsave('test_route_b_base.png', result)
print("Saved test_route_b_base.png")

# ---- China crop ----
x1 = int((73 + 180) / 360 * 10800)
x2 = int((136 + 180) / 360 * 10800)
y1 = int((90 - 54) / 180 * 5400)
y2 = int((90 - 18) / 180 * 5400)
china_crop = result[y1:y2, x1:x2]
plt.imsave('test_route_b_china_crop.png', china_crop)
print(f"Saved China crop: {china_crop.shape}")
