#!/usr/bin/env python3
"""从真实风景 RAW 的相机预览重建一个可跑的 Bayer RAW 示例。

注意：这不是传感器原始 CRW 的逐像素导出；CRW 原始文件下载受限，
这里用同一张 RAW 的相机预览重建 Bayer 数据，用于教学流水线演示。
输出 data/landscape.raw / landscape.meta，不覆盖 data/sample.*。
"""
import numpy as np
from PIL import Image, ImageEnhance
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
im = Image.open(ROOT / "docs" / "images" / "landscape_raw.jpg").convert("RGB")
im = im.resize((2880, 1920), Image.LANCZOS)
a = np.asarray(im, dtype=np.float32) / 255.0
# sRGB -> linear
lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
# 轻微暖色偏，给 AWB 一点工作
lin[..., 0] *= 1.10
lin[..., 2] *= 0.82
h, w, _ = lin.shape
raw = np.zeros((h, w), dtype=np.float32)
for y in range(h):
    for x in range(w):
        if y % 2 == 0 and x % 2 == 0:
            v = lin[y, x, 0]
        elif y % 2 == 1 and x % 2 == 1:
            v = lin[y, x, 2]
        else:
            v = lin[y, x, 1]
        raw[y, x] = v
# 黑电平 2047，白电平 15000；加一点读出噪声
white, black = 15000, 2047
dn = np.clip(raw * (white - black) + black, 0, white)
rng = np.random.default_rng(9)
dn = np.clip(dn + rng.normal(0, 1.6, dn.shape), 0, white)
dn.astype("<u2").tofile(ROOT / "data" / "landscape.raw")

# sRGB 的 XYZ->RGB 矩阵，取逆作为相机 RGB->XYZ；CCM 再乘回来近似恒等
M = np.array([[3.2406, -1.5372, -0.4986],
              [-0.9689, 1.8758, 0.0415],
              [0.0557, -0.2040, 1.0570]], dtype=np.float64)
inv = np.linalg.inv(M)
meta = f"""# 2880x1920 16bit little-endian Bayer RAW
width 2880
height 1920
bayer RGGB
black 2047 2047 2047 2048
white 15000
wb 1.10 1.000 1.22
cam_to_xyz {' '.join(f'{v:.8f}' for v in inv.reshape(-1))}
camera Canon EOS D60 (landscape preview reconstruction)
"""
(ROOT / "data" / "landscape.meta").write_text(meta, encoding="utf-8")
print("wrote", ROOT / "data" / "landscape.raw", dn.shape, dn.nbytes)
