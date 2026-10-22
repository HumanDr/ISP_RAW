#!/usr/bin/env python3
"""不依赖 PPT 的 ISP 动画讲解视频。

风格：深色底、米金配色、细线、实际 ISP 图像变化、底部衬线字幕。
输出：docs/ISP_Raw_Animated_5min.mp4
"""
import argparse
import json
import math
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMG = DOCS / "images"
WORK = ROOT / "out" / "landscape_anim"
WORK.mkdir(parents=True, exist_ok=True)
FF = ROOT / ".pylibs" / "imageio_ffmpeg" / "binaries" / "ffmpeg-linux-x86_64-v7.0.2"
W, H, FPS = 1920, 1080, 24
TAIL = 0.45
LEAD = 0.15

sys.path.insert(0, str(ROOT / "tools"))
import anim_script_landscape as S

BG = (5, 6, 9)
CREAM = (246, 232, 201)
GOLD = (226, 173, 92)
MUTED = (145, 136, 121)
DIM = (82, 78, 70)
RED = (214, 104, 78)
GREEN = (116, 184, 148)
BLUE = (102, 154, 202)
WHITE = (238, 235, 226)

FONT_SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
FONT_SERIF_B = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
FONT_SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
_fcache = {}


def font(size, kind="serif"):
    key = (size, kind)
    if key not in _fcache:
        path = {"serif": FONT_SERIF, "serif_b": FONT_SERIF_B,
                "sans": FONT_SANS, "mono": FONT_MONO}[kind]
        _fcache[key] = ImageFont.truetype(path, size)
    return _fcache[key]


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * clamp(t)


def alpha_at(t, start, end, fade=0.5):
    return smooth((t - start) / fade) * smooth((end - t) / fade)


def text(d, xy, s, size, fill=CREAM, kind="serif", anchor="la", alpha=255):
    if alpha <= 0:
        return
    col = tuple(fill) + (int(alpha),)
    d.text(xy, s, font=font(size, kind), fill=col, anchor=anchor)


def line(d, xy, fill=GOLD, width=2, alpha=255):
    d.line(xy, fill=tuple(fill) + (int(alpha),), width=width)


def make_bg():
    yy, xx = np.mgrid[0:H, 0:W]
    # 很轻的径向渐变，中心稍亮
    cx, cy = W * 0.5, H * 0.45
    r = np.sqrt(((xx - cx) / W) ** 2 + ((yy - cy) / H) ** 2)
    base = np.clip(10 - 7 * r, 3, 12)
    arr = np.stack([base * 0.85, base * 0.92, base * 1.05], axis=2)
    arr += np.random.default_rng(7).normal(0, 0.7, arr.shape)
    arr = np.clip(arr, 2, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGB")
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(11)
    for _ in range(240):
        x, y = int(rng.integers(0, W)), int(rng.integers(0, H))
        v = int(rng.integers(18, 65))
        d.point((x, y), fill=(v, v, max(10, v - 8)))
    return im


BG_IMG = make_bg()


def load_img(name):
    return Image.open(IMG / name).convert("RGB")


STAGE = {i: load_img(f"landscape/stage_{i:02d}.png") for i in
         [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]}
FINAL = load_img("landscape/final_full.png")
BAYER = load_img("bayer_pattern.png")
DEMO_CMP = load_img("landscape/demosaic_compare.png")
DEMO_CMP = load_img("demosaic_compare.png")


def paste_fit(canvas, im, box, zoom=1.0, alpha=255, pan=(0.0, 0.0),
              border=True, radius=6):
    if alpha <= 0:
        return
    x, y, w, h = [int(v) for v in box]
    iw, ih = im.size
    s = max(w / iw, h / ih) * zoom
    nw, nh = int(iw * s), int(ih * s)
    im2 = im.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) / 2 + pan[0] * (nw - w) / 2
    top = (nh - h) / 2 + pan[1] * (nh - h) / 2
    left = int(clamp(left, 0, max(0, nw - w)))
    top = int(clamp(top, 0, max(0, nh - h)))
    im2 = im2.crop((left, top, left + w, top + h))
    if alpha < 255:
        im2 = im2.convert("RGBA")
        im2.putalpha(int(alpha))
    canvas.paste(im2, (x, y), im2 if im2.mode == "RGBA" else None)
    if border:
        d = ImageDraw.Draw(canvas, "RGBA")
        c = tuple(GOLD) + (int(alpha * 0.55),)
        L = 22
        for (px, py, dx, dy) in [(x, y, 1, 1), (x + w, y, -1, 1),
                                 (x, y + h, 1, -1), (x + w, y + h, -1, -1)]:
            d.line((px, py, px + dx * L, py), fill=c, width=2)
            d.line((px, py, px, py + dy * L), fill=c, width=2)


def scene_title(d, kicker, title, t, dur):
    a = alpha_at(t, 0.0, dur, 0.6)
    text(d, (118, 78), kicker, 18, GOLD, "sans", alpha=a)
    text(d, (118, 106), title, 46, CREAM, "serif_b", alpha=a)
    line(d, (118, 168, 118 + int(150 * smooth(t / 0.9)), 168), GOLD, 2, a)


def fig(d, idx, caption, alpha=150):
    text(d, (118, 1032), f"FIG. {idx:02d} — {caption}", 14, MUTED, "mono", alpha=alpha)


def bayer_tile(size=12, cell=34, reveal=1.0, alpha=255):
    tile = Image.new("RGBA", (size * cell, size * cell), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    # 取画面中央附近的一块，保证有内容（RAW 在模块加载时只读一次）
    crop = RAW[1500:1500 + size, 2600:2600 + size].astype(np.float32)
    crop = np.clip((crop - BLACK) / (WHITE - BLACK), 0, 1)
    for yy in range(size):
        for xx in range(size):
            k = yy * size + xx
            if k / (size * size) > reveal:
                continue
            even_y, even_x = (yy % 2 == 0), (xx % 2 == 0)
            if even_y and even_x:
                base, c = crop[yy, xx], (205, 92, 72)
            elif (not even_y) and (not even_x):
                base, c = crop[yy, xx], (92, 132, 200)
            else:
                base, c = crop[yy, xx], (105, 178, 132)
            v = 0.22 + 0.78 * (base ** 0.7)
            col = tuple(int(x * v) for x in c) + (alpha,)
            d.rectangle((xx * cell, yy * cell, (xx + 1) * cell, (yy + 1) * cell), fill=col)
    # 细网格
    for i in range(size + 1):
        d.line((i * cell, 0, i * cell, size * cell), fill=(10, 10, 10, 120), width=1)
        d.line((0, i * cell, size * cell, i * cell), fill=(10, 10, 10, 120), width=1)
    return tile


RAW = np.fromfile(ROOT / "data" / "landscape.raw", dtype="<u2").reshape(2056, 3088)
BLACK, WHITE = 127, 4000
raw_norm = np.clip((RAW.astype(np.float32) - BLACK) / (WHITE - BLACK), 0, 1)
hist_raw, _ = np.histogram(RAW[::4, ::4], bins=128, range=(0, 4096))
hist_blc, _ = np.histogram(raw_norm[::4, ::4], bins=128, range=(0, 1))
hist_raw = np.log1p(hist_raw).astype(np.float32)
hist_blc = np.log1p(hist_blc).astype(np.float32)
hist_raw /= max(1, hist_raw.max())
hist_blc /= max(1, hist_blc.max())
# 用同一 DN 横轴画“减黑电平后”，才能和 RAW 直方图对比
hist_blc_dn, _ = np.histogram(
    np.clip((RAW.astype(np.float32) - BLACK) / (WHITE - BLACK), 0, 1)[::4, ::4] * 4096,
    bins=128, range=(0, 4096))
hist_blc_dn = np.log1p(hist_blc_dn).astype(np.float32)
hist_blc_dn /= max(1, hist_blc_dn.max())

# 从 stage 12 计算 Y/U/V，用于动画
_rgb12 = np.asarray(STAGE[12].resize((720, 480)), dtype=np.float32) / 255.0
Y12 = 0.2126 * _rgb12[..., 0] + 0.7152 * _rgb12[..., 1] + 0.0722 * _rgb12[..., 2]
U12 = (_rgb12[..., 2] - Y12) / 1.8556
V12 = (_rgb12[..., 0] - Y12) / 1.5748


def channel_img(a, mode):
    if mode == "Y":
        a = np.clip(a, 0, 1)
        arr = np.stack([a * 255] * 3, axis=2)
    else:
        # 室内场景色度很平，先做百分位拉伸，才看得到 U/V 的结构
        lo, hi = np.percentile(a, [2, 98])
        a = np.clip((a - lo) / max(1e-6, hi - lo), 0, 1)
        if mode == "U":
            arr = np.stack([20 + 40 * a, 60 + 140 * a, 130 + 80 * a], axis=2)
        else:
            arr = np.stack([70 + 170 * a, 30 + 110 * a, 50 + 100 * a], axis=2)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


Y_IMG = channel_img(Y12, "Y")
U_IMG = channel_img(U12, "U")
V_IMG = channel_img(V12, "V")


def draw_hist(d, box, hist, color, progress=1.0, baseline=True, alpha=255):
    x, y, w, h = box
    if baseline:
        line(d, (x, y + h, x + w, y + h), DIM, 1, alpha)
    n = max(2, int(len(hist) * progress))
    pts = []
    for i in range(n):
        px = x + i / (len(hist) - 1) * w
        py = y + h - hist[i] * h * 0.9
        pts.append((px, py))
    if len(pts) > 1:
        d.line(pts, fill=tuple(color) + (alpha,), width=2)


def draw_matrix(d, x, y, m, cell=74, alpha=255):
    for r in range(3):
        for c in range(3):
            xx, yy = x + c * (cell + 8), y + r * (cell + 8)
            d.rectangle((xx, yy, xx + cell, yy + cell), outline=tuple(GOLD) + (alpha // 2,), width=1)
            text(d, (xx + cell // 2, yy + cell // 2), f"{m[r * 3 + c]:+.2f}", 15,
                 CREAM, "mono", anchor="mm", alpha=alpha)


def draw_gamma(d, x, y, w, h, progress=1.0, alpha=255):
    line(d, (x, y + h, x + w, y + h), DIM, 1, alpha)
    line(d, (x, y, x, y + h), DIM, 1, alpha)
    text(d, (x + w + 12, y + h - 16), "linear", 13, MUTED, "mono", alpha=alpha)
    text(d, (x, y - 24), "sRGB", 13, GOLD, "mono", alpha=alpha)
    pts = []
    for i in range(121):
        u = i / 120
        v = 12.92 * u if u <= 0.0031308 else 1.055 * u ** (1 / 2.4) - 0.055
        pts.append((x + u * w, y + h - v * h))
    n = max(2, int(len(pts) * progress))
    d.line(pts[:n], fill=tuple(GOLD) + (alpha,), width=2)
    mx = x + w * progress
    my = y + h - (1.055 * progress ** (1 / 2.4) - 0.055) * h
    d.ellipse((mx - 5, my - 5, mx + 5, my + 5), fill=tuple(CREAM) + (alpha,))


def draw_gain_bars(d, x, y, gains, alpha=255):
    for i, (name, g, col) in enumerate(zip("RGB", gains, [RED, GREEN, BLUE])):
        bh = int(80 * clamp(g / 2.8))
        d.rectangle((x + i * 44, y - bh, x + i * 44 + 24, y),
                    fill=tuple(col) + (int(alpha * 0.75),))
        text(d, (x + i * 44 + 12, y + 12), name, 14, MUTED, "mono", anchor="ma", alpha=alpha)
        text(d, (x + i * 44 + 12, y - bh - 20), f"{g:.2f}", 12, CREAM, "mono",
             anchor="ma", alpha=alpha)


def draw_hue_wheel(d, cx, cy, r, t, alpha=255):
    for i in range(120):
        a0 = i / 120 * 2 * math.pi
        a1 = (i + 1.2) / 120 * 2 * math.pi
        import colorsys
        rr, gg, bb = colorsys.hsv_to_rgb(i / 120, 0.55, 0.9)
        col = (int(rr * 255), int(gg * 255), int(bb * 255), int(alpha * 0.8))
        d.arc((cx - r, cy - r, cx + r, cy + r), math.degrees(a0), math.degrees(a1),
              fill=col, width=16)
    a = t * 0.8
    mx, my = cx + r * 0.78 * math.cos(a), cy + r * 0.78 * math.sin(a)
    d.ellipse((mx - 7, my - 7, mx + 7, my + 7), fill=tuple(CREAM) + (alpha,))


# ---------------------------------------------------------------- scenes
def scene_intro(t, dur):
    c = BG_IMG.copy()
    d = ImageDraw.Draw(c, "RGBA")
    a = alpha_at(t, 0, dur, 0.7)
    text(d, (118, 142), "A FIVE-MINUTE JOURNEY", 16, GOLD, "mono", alpha=a)
    text(d, (118, 182), "当你按下快门", 68, CREAM, "serif_b", alpha=a)
    text(d, (120, 286), "从光，到 RAW，再到彩色照片", 28, (205, 194, 174), "serif", alpha=a)
    line(d, (120, 352, 120 + int(280 * smooth(t / 1.2)), 352), GOLD, 2, a)

    tile = bayer_tile(11, 30, reveal=smooth(t / 3.0), alpha=int(255 * a))
    c.paste(tile, (120, 470), tile)
    text(d, (120, 826), "单通道 · Bayer · 16 bit", 18, MUTED, "sans", alpha=a)

    ea = smooth((t - 2.0) / 2.0) * a
    paste_fit(c, FINAL, (840, 210, 860, 484), zoom=1.04 - 0.04 * smooth(t / 6), alpha=int(255 * ea))
    text(d, (840, 714), "20 个 stage 之后的输出", 18, MUTED, "sans", alpha=ea)
    return c


def scene_raw(t, dur):
    c = BG_IMG.copy()
    d = ImageDraw.Draw(c, "RGBA")
    scene_title(d, "01 / 输入", "RAW 不是图片", t, dur)
    a = alpha_at(t, 0, dur, 0.6)

    # 左侧：文件卡片 + 字节
    d.rectangle((118, 226, 720, 760), outline=tuple(GOLD) + (70,), width=1)
    text(d, (146, 250), "风景 RAW", 30, CREAM, "serif_b", alpha=a)
    text(d, (146, 300), "12,697,856 bytes", 18, MUTED, "mono", alpha=a)
    raw = np.fromfile(ROOT / "data" / "landscape.raw", dtype=np.uint8, count=192)
    rows = []
    for i in range(0, 128, 16):
        rows.append(" ".join(f"{b:02x}" for b in raw[i:i + 16]))
    nrows = int(smooth(t / 3.0) * len(rows)) + 1
    for i, row in enumerate(rows[:nrows]):
        text(d, (146, 366 + i * 30), f"{i * 16:04x}  {row}", 15,
             (185, 174, 154), "mono", alpha=a)

    # 右侧：Bayer 网格 + meta
    tile = bayer_tile(12, 40, reveal=smooth((t - 1.0) / 3.0), alpha=int(255 * a))
    c.paste(tile, (900, 224), tile)
    text(d, (900, 728), "RGGB：G 占 50%，R/B 各 25%", 19, MUTED, "sans", alpha=a)

    meta = [("width", "3088"), ("height", "2056"), ("bayer", "RGGB"),
            ("black", "127 … 127"), ("white", "4000")]
    for i, (k, v) in enumerate(meta):
        ma = smooth((t - 3.0 - i * 0.6) / 0.8) * a
        text(d, (1480, 238 + i * 54), k, 17, GOLD, "mono", alpha=ma)
        text(d, (1620, 238 + i * 54), v, 17, CREAM, "mono", alpha=ma)
    text(d, (1480, 560), "meta 是它的说明书", 22, CREAM, "serif", alpha=a)
    text(d, (1480, 602), "少一个字段，ISP 就只能猜", 17, MUTED, "sans", alpha=a)
    fig(d, 1, "RAW IS NOT AN IMAGE", int(130 * a))
    return c


def scene_pipeline(t, dur):
    c = BG_IMG.copy()
    d = ImageDraw.Draw(c, "RGBA")
    scene_title(d, "02 / 全景", "三个域，二十步", t, dur)
    a = alpha_at(t, 0, dur, 0.6)
    lanes = [
        ("RAW 域 · 修数据", ["RAW", "BLC", "LSC", "BPC/DPC", "NR RAW", "AWB", "Demosaic"], 286, (66, 104, 150)),
        ("RGB 域 · 算颜色", ["NR Color", "X-Talk", "CCM", "HDR/WDR", "Gamma", "Color Space"], 520, (150, 108, 62)),
        ("YUV 域 · 修观感", ["NR Luma", "Edge", "Contrast", "NR Chroma", "Hue/Sat", "Scale", "Encoder"], 754, (62, 112, 82)),
    ]
    active = int(clamp(t / 1.35, 0, 19))
    idx = 0
    for li, (label, names, y, col) in enumerate(lanes):
        text(d, (90, y - 54), label, 17, GOLD, "sans", alpha=a)
        n = len(names)
        bw, gap = 210, 16
        x0 = 150
        for j, name in enumerate(names):
            x = x0 + j * (bw + gap)
            on = idx <= active
            cur = idx == active
            fill = (18, 20, 24) if not on else (28, 26, 22)
            outline = tuple(col) + (110,) if not cur else tuple(GOLD) + (255,)
            d.rounded_rectangle((x, y, x + bw, y + 92), radius=6, fill=fill,
                                outline=outline, width=2 if cur else 1)
            text(d, (x + 18, y + 14), f"{idx:02d}", 13, GOLD if on else DIM, "mono", alpha=a)
            text(d, (x + 18, y + 38), name, 19, CREAM if on else DIM, "serif_b", alpha=a)
            if j:
                d.line((x - gap, y + 46, x - 2, y + 46), fill=tuple(MUTED) + (80,), width=1)
            if cur:
                d.ellipse((x + bw - 24, y + 12, x + bw - 14, y + 22), fill=tuple(GOLD) + (255,))
            idx += 1
    text(d, (150, 912), "RAW → RGB → YUV", 22, CREAM, "serif", alpha=a)
    text(d, (150, 948), "线性的运算，放在 Gamma 之前", 16, MUTED, "sans", alpha=a)
    fig(d, 2, "TWENTY STAGES, THREE DOMAINS", int(120 * a))
    return c


def stage_panel(c, d, im, box, label, t, alpha):
    paste_fit(c, im, box, alpha=int(alpha))
    text(d, (box[0], box[1] - 30), label, 16, GOLD, "sans", alpha=alpha)


def scene_rawfix(t, dur):
    c = BG_IMG.copy()
    d = ImageDraw.Draw(c, "RGBA")
    scene_title(d, "03 / RAW 域", "先修数据", t, dur)
    a = alpha_at(t, 0, dur, 0.6)
    # 阶段切换
    bounds = [0, 6.32, 10.41, 14.34, 19.22, 23.34, dur]
    names = ["01 / BLC 黑电平补偿", "02 / LSC 镜头阴影矫正", "03 / BPC/DPC 坏点矫正",
             "04 / NR RAW 降噪", "05 / AWB 白平衡", "06 / Demosaic 去马赛克"]
    k = 0
    for i in range(6):
        if t >= bounds[i]:
            k = i
    # 主图：根据阶段选图，交叉淡入
    if k == 0:
        im = STAGE[0]
    elif k == 1:
        im = STAGE[2]
    elif k == 2:
        im = STAGE[3]
    elif k == 3:
        im = STAGE[4]
    elif k == 4:
        im = STAGE[5]
    else:
        im = STAGE[6]
    paste_fit(c, im, (118, 220, 760, 506), alpha=int(240 * a))
    text(d, (118, 752), names[k], 22, CREAM, "serif_b", alpha=a)
    text(d, (118, 790), "同一张画面，RAW 域内部的真实变化", 16, MUTED, "sans", alpha=a)

    # 右侧动态图
    rx, ry, rw, rh = 1040, 300, 650, 300
    if k == 0:
        draw_hist(d, (rx, ry + 40, 300, 190), hist_raw, MUTED, 1.0, True, int(180 * a))
        draw_hist(d, (rx + 390, ry + 40, 300, 190), hist_blc_dn, GOLD,
                  smooth(t / 7), True, int(255 * a))
        text(d, (rx + 5, ry + 5), "RAW 原始", 15, MUTED, "sans", alpha=a)
        text(d, (rx + 395, ry + 5), "减黑电平后", 15, GOLD, "sans", alpha=a)
        text(d, (rx + 315, ry + 115), "127 → 0", 17, CREAM, "sans", alpha=a)
        text(d, (rx, ry + 270), "同一 DN 横轴：尖峰从 127 移到 0", 14, MUTED, "sans", alpha=a)
        text(d, (rx, ry + 330), "先减偏置，再乘增益", 16, MUTED, "sans", alpha=a)
    elif k == 1:
        # 径向暗角示意
        for i in range(5):
            rr = 60 + i * 58
            d.arc((rx + rw // 2 - rr, ry + rh // 2 - rr, rx + rw // 2 + rr, ry + rh // 2 + rr),
                  0, 360, fill=tuple(GOLD) + (int((60 - i * 8) * a),), width=2)
        text(d, (rx, ry - 8), "四角增益 > 1", 20, CREAM, "serif", alpha=a)
        text(d, (rx, ry + 360), "cos⁴ 衰减，用径向增益补回来", 16, MUTED, "sans", alpha=a)
    elif k == 2:
        text(d, (rx, ry - 8), "孤立极值 → 同色中值", 20, CREAM, "serif", alpha=a)
        # 5x5 Bayer 小网格：中心坏点，金色是同色 4 邻域
        gx, gy, cell = rx + 155, ry + 35, 44
        for yy in range(5):
            for xx in range(5):
                is_center = (xx == 2 and yy == 2)
                is_same = (abs(xx - 2) + abs(yy - 2) == 1)
                fill = (70, 26, 22) if is_center else ((38, 32, 20) if is_same else (16, 17, 20))
                out = RED if is_center else (GOLD if is_same else (55, 54, 50))
                d.rectangle((gx + xx * cell, gy + yy * cell,
                             gx + (xx + 1) * cell, gy + (yy + 1) * cell),
                            fill=fill, outline=tuple(out) + (200,), width=2 if (is_center or is_same) else 1)
        pulse = 0.5 + 0.5 * math.sin(t * 4)
        d.ellipse((gx + 2 * cell - 7, gy + 2 * cell - 7,
                   gx + 2 * cell + 7, gy + 2 * cell + 7),
                  outline=tuple(CREAM) + (int(180 + 60 * pulse),), width=2)
        text(d, (gx - 10, gy + 5 * cell + 14), "中心：坏点", 14, RED, "sans", alpha=a)
        text(d, (gx + 2 * cell + 20, gy + 5 * cell + 14), "金色：同色 4 邻域", 14, GOLD, "sans", alpha=a)
        text(d, (rx, ry + 360), "坏点不修，去马赛克后会扩散", 16, MUTED, "sans", alpha=a)
    elif k == 3:
        text(d, (rx, ry - 8), "同色邻居双边滤波", 20, CREAM, "serif", alpha=a)
        paste_fit(c, STAGE[3], (rx, ry + 30, 300, 200), alpha=int(235 * a))
        paste_fit(c, STAGE[4], (rx + 330, ry + 30, 300, 200), alpha=int(235 * a))
        text(d, (rx, ry + 244), "降噪前", 14, MUTED, "sans", alpha=a)
        text(d, (rx + 330, ry + 244), "降噪后", 14, GOLD, "sans", alpha=a)
        text(d, (rx, ry + 360), "只采样 dx+dy 为偶数的同色像素", 16, MUTED, "sans", alpha=a)
    elif k == 4:
        gains = [1.43, 1.0, 2.58]
        draw_gain_bars(d, rx + 80, ry + 250, gains, int(255 * a))
        text(d, (rx, ry - 8), "R / G / B 增益", 20, CREAM, "serif", alpha=a)
        text(d, (rx, ry + 360), "把中性色拉回 R = G = B", 16, MUTED, "sans", alpha=a)
    else:
        tile = bayer_tile(10, 34, reveal=smooth((t - 44) / 4), alpha=int(255 * a))
        c.paste(tile, (rx + 90, ry + 20), tile)
        text(d, (rx, ry - 8), "单通道 → 三通道", 20, CREAM, "serif", alpha=a)
        text(d, (rx, ry + 360), "每个像素缺两个颜色，靠邻居插值", 16, MUTED, "sans", alpha=a)

    # 底部进度刻度
    for i, name in enumerate(names):
        xx = 118 + i * 290
        on = i <= k
        d.line((xx, 850, xx + 260, 850), fill=tuple(GOLD if on else DIM) + (180,), width=3 if on else 1)
        text(d, (xx, 866), name.split(" / ")[1], 13, MUTED if not on else CREAM, "sans", alpha=a)
    fig(d, 3, "REPAIRING THE SENSOR DATA", int(110 * a))
    return c


def scene_demosaic(t, dur):
    c = BG_IMG.copy()
    d = ImageDraw.Draw(c, "RGBA")
    scene_title(d, "04 / 去马赛克", "猜颜色", t, dur)
    a = alpha_at(t, 0, dur, 0.6)
    # 左：Bayer 网格；右：RGB
    reveal = smooth((t - 0.5) / 4)
    tile = bayer_tile(10, 42, reveal=reveal, alpha=int(255 * a))
    c.paste(tile, (160, 250), tile)
    text(d, (160, 690), "输入：单通道 Bayer", 17, MUTED, "sans", alpha=a)
    paste_fit(c, STAGE[6], (820, 230, 780, 520), alpha=int(255 * smooth((t - 4) / 3) * a))
    text(d, (820, 772), "输出：三通道 RGB", 17, MUTED, "sans", alpha=a)

    # 12s 之后切到 100% 对比
    if t > 13:
        fade = smooth((t - 13) / 2) * a
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.rectangle((90, 200, 1830, 900), fill=(5, 6, 9, int(235 * fade)))
        c = c.convert("RGBA")
        c.alpha_composite(ov)
        c = c.convert("RGB")
        d = ImageDraw.Draw(c, "RGBA")
        text(d, (120, 220), "100% 裁剪 · 左：双线性 / 右：MHC", 22, CREAM, "serif", alpha=fade)
        # 两个裁切面板
        cmp_img = DEMO_CMP
        boxes = [(14, 120, 705, 635), (835, 120, 1526, 635)]
        for i, bb in enumerate(boxes):
            im = cmp_img.crop(bb).resize((760, 540), Image.LANCZOS)
            c.paste(im, (150 + i * 820, 290))
            text(d, (150 + i * 820, 840), ["bilinear", "Malvar-He-Cutler"][i], 19,
                 MUTED if i == 0 else GOLD, "mono", alpha=fade)
        ca = smooth((t - 19) / 2) * fade
        text(d, (150, 900), "G = (G左+G右+G上+G下)/4", 20, CREAM, "sans", alpha=ca)
        text(d, (150, 936), "MHC：5×5 加权窗口 + 梯度修正", 20, GOLD, "sans", alpha=ca)
    fig(d, 4, "DEMOSAIC: GUESSING COLOR", int(110 * a))
    return c


def scene_rgb(t, dur):
    c = BG_IMG.copy()
    d = ImageDraw.Draw(c, "RGBA")
    scene_title(d, "05 / RGB 域", "把颜色算对", t, dur)
    a = alpha_at(t, 0, dur, 0.6)
    if t < 12:
        # CCM 前后
        paste_fit(c, STAGE[8], (118, 220, 740, 500), alpha=int(240 * a))
        paste_fit(c, STAGE[9], (900, 220, 740, 500), alpha=int(240 * a))
        text(d, (118, 732), "CCM 前", 18, MUTED, "sans", alpha=a)
        text(d, (900, 732), "CCM 后", 18, GOLD, "sans", alpha=a)
        draw_matrix(d, 118, 790, [2.0429, -1.1233, 0.0804, -0.2970, 1.6431, -0.3461, 0.0100, -0.7474, 1.7374], cell=48, alpha=int(220 * a))
        text(d, (118, 980), "相机 RGB → XYZ → linear sRGB", 17, MUTED, "sans", alpha=a)
    elif t < 20:
        paste_fit(c, STAGE[9], (118, 220, 740, 500), alpha=int(240 * a))
        paste_fit(c, STAGE[10], (900, 220, 740, 500), alpha=int(240 * a))
        text(d, (118, 732), "HDR 前：高光接近硬 clip", 16, MUTED, "sans", alpha=a)
        text(d, (900, 732), "HDR 后：只压 > 1 的高光", 16, GOLD, "sans", alpha=a)
        text(d, (118, 790), "避免品红高光，0..1 的颜色不动", 18, CREAM, "serif", alpha=a)
    elif t < 30:
        paste_fit(c, STAGE[11], (118, 220, 720, 480), alpha=int(240 * a))
        text(d, (118, 730), "Gamma：自动曝光 + sRGB", 18, GOLD, "sans", alpha=a)
        draw_gamma(d, 960, 300, 620, 340, smooth((t - 20) / 5), int(255 * a))
        text(d, (960, 690), "线性光不能直接写 8bit", 18, MUTED, "sans", alpha=a)
    else:
        # RGB -> YUV 三分量
        for i, (im, name, col) in enumerate([(Y_IMG, "Y 亮度", GREEN), (U_IMG, "U 色度", BLUE), (V_IMG, "V 色度", RED)]):
            xx = 150 + i * 570
            paste_fit(c, im, (xx, 250, 450, 300), alpha=int(245 * a))
            text(d, (xx, 570), name, 18, col, "sans", alpha=a)
        text(d, (150, 650), "RGB → YUV(BT.709)", 26, CREAM, "serif", alpha=a)
        text(d, (150, 700), "Y 保留细节，U/V 可以降分辨率", 17, MUTED, "sans", alpha=a)
    fig(d, 5, "COLOR, DYNAMIC RANGE, GAMMA", int(110 * a))
    return c


def scene_yuv(t, dur):
    c = BG_IMG.copy()
    d = ImageDraw.Draw(c, "RGBA")
    scene_title(d, "06 / YUV 域", "修观感，再编码", t, dur)
    a = alpha_at(t, 0, dur, 0.6)
    # 三个通道始终在左侧
    for i, (im, name, col) in enumerate([(Y_IMG, "Y", GREEN), (U_IMG, "U", BLUE), (V_IMG, "V", RED)]):
        xx = 110 + i * 240
        paste_fit(c, im, (xx, 250, 220, 150), alpha=int(235 * a))
        text(d, (xx, 418), name, 16, col, "mono", alpha=a)

    if t < 8:
        text(d, (900, 260), "YUV", 54, CREAM, "serif_b", alpha=a)
        text(d, (900, 334), "亮度 + 两个色度", 22, MUTED, "serif", alpha=a)
        text(d, (900, 390), "人眼对色度分辨率不敏感", 17, MUTED, "sans", alpha=a)
        text(d, (900, 820), "U/V 的对比度已拉伸，方便观察结构", 14, MUTED, "sans", alpha=a)
    elif t < 15:
        paste_fit(c, STAGE[13], (890, 240, 430, 287), alpha=int(240 * a))
        paste_fit(c, STAGE[14], (1345, 240, 430, 287), alpha=int(240 * a))
        text(d, (890, 550), "Y 降噪", 16, MUTED, "sans", alpha=a)
        text(d, (1345, 550), "+ 边缘增强", 16, GOLD, "sans", alpha=a)
        text(d, (890, 620), "只改 Y，U/V 不动", 20, CREAM, "serif", alpha=a)
    elif t < 22:
        paste_fit(c, STAGE[16], (900, 220, 640, 420), alpha=int(240 * a))
        text(d, (900, 680), "U/V 中值降噪", 20, CREAM, "serif", alpha=a)
    else:
        draw_hue_wheel(d, 1180, 440, 170, t * 0.6, int(255 * a))
        text(d, (900, 260), "色相 / 饱和度", 24, CREAM, "serif", alpha=a)
        text(d, (900, 300), "在 YUV 平面里旋转、缩放", 17, MUTED, "sans", alpha=a)

    text(d, (110, 820), "Y 保留细节，U/V 更强降噪", 18, MUTED, "sans", alpha=a)
    text(d, (110, 860), "420：U/V 各降一半分辨率", 18, GOLD, "sans", alpha=a)
    fig(d, 6, "THE HUMAN-VISION DOMAIN", int(110 * a))
    return c


def scene_result(t, dur):
    c = BG_IMG.copy()
    d = ImageDraw.Draw(c, "RGBA")
    scene_title(d, "07 / 结果", "1544 × 868，约 3 秒", t, dur)
    a = alpha_at(t, 0, dur, 0.6)
    # 前后滑块
    w, h = 900, 506
    x, y = 140, 230
    if t < 3:
        paste_fit(c, FINAL, (x, y, w, h), alpha=int(255 * smooth(t / 3) * a))
    else:
        p = smooth((t - 4) / 10)
        left = STAGE[0].resize((w, h), Image.LANCZOS)
        right = FINAL.resize((w, h), Image.LANCZOS)
        c.paste(left, (x, y))
        cut = int(w * (0.12 + 0.76 * p))
        c.paste(right.crop((0, 0, cut, h)), (x, y))
        d.line((x + cut, y, x + cut, y + h), fill=tuple(CREAM) + (220,), width=3)
        text(d, (x, y + h + 20), "RAW（左） → ISP（右）", 16, MUTED, "sans", alpha=a)

    stats = [("20", "stage"), ("3s", "单线程"), ("0", "分步 vs 内存"), ("1.5K", "× 868")]
    for i, (big, small) in enumerate(stats):
        yy = 250 + i * 110
        text(d, (1160, yy), big, 44, GOLD if i == 0 else CREAM, "serif_b", alpha=a)
        text(d, (1330, yy + 18), small, 16, MUTED, "sans", alpha=a)
    text(d, (1160, 760), "out/final.png", 17, GOLD, "mono", alpha=a)
    text(d, (1160, 794), "PNG + 可选 YUV420", 17, MUTED, "sans", alpha=a)
    fig(d, 7, "THE RESULT", int(110 * a))
    return c


def scene_summary(t, dur):
    c = BG_IMG.copy()
    d = ImageDraw.Draw(c, "RGBA")
    a = alpha_at(t, 0, dur, 0.7)
    text(d, (118, 160), "08 / 总结", 18, GOLD, "sans", alpha=a)
    text(d, (118, 204), "三域拆开，ISP 就不再是黑魔法", 46, CREAM, "serif_b", alpha=a)
    items = [("01", "RAW 域修数据", "BLC · LSC · DPC · NR · AWB · Demosaic", 340),
             ("02", "RGB 域算颜色", "NR Color · X-Talk · CCM · WDR · Gamma", 500),
             ("03", "YUV 域修观感", "Luma · Edge · Chroma · Hue/Sat · Scale", 660)]
    for i, (num, name, desc, yy) in enumerate(items):
        ia = smooth((t - 1.0 - i * 1.1) / 0.8) * a
        text(d, (118, yy), num, 18, GOLD, "mono", alpha=ia)
        text(d, (190, yy - 12), name, 30, CREAM, "serif_b", alpha=ia)
        text(d, (190, yy + 32), desc, 16, MUTED, "sans", alpha=ia)
    line(d, (118, 778, 118 + int(300 * smooth((t - 6) / 1)), 778), GOLD, 2, a)
    text(d, (118, 806), "先跑通  →  再拆开  →  最后替换算法", 24, CREAM, "serif", alpha=a)
    text(d, (118, 910), "谢谢", 58, GOLD, "serif_b", alpha=smooth((t - 6) / 1) * a)
    text(d, (300, 940), "欢迎提问 / 一起改代码", 18, MUTED, "sans", alpha=smooth((t - 6.5) / 1) * a)
    fig(d, 8, "THREE DOMAINS, ONE PIPELINE", int(110 * a))
    return c


SCENES = [
    ("intro", scene_intro), ("raw", scene_raw), ("pipeline", scene_pipeline),
    ("rawfix", scene_rawfix), ("demosaic", scene_demosaic), ("rgb", scene_rgb),
    ("yuv", scene_yuv), ("result", scene_result), ("summary", scene_summary),
]


def audio_duration(p):
    r = subprocess.run([str(FF), "-hide_banner", "-i", str(p)],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stdout.decode(errors="ignore"))
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def build_timeline():
    starts, durs = [], []
    total = 0.0
    for i, (key, _) in enumerate(SCENES, 1):
        p = WORK / "voice" / f"{i:02d}_{key}.mp3"
        d = audio_duration(p)
        if i == 1:
            d += 1.0
        starts.append(total)
        durs.append(d)
        total += d + TAIL
    return starts, durs, total


def wrap(s, width=34):
    out, cur = [], ""
    for ch in s:
        cur += ch
        if len(cur) >= width and ch in "，。；：！？、":
            out.append(cur); cur = ""
    if cur:
        out.append(cur)
    # 二次按长度硬切
    res = []
    for line in out:
        while len(line) > width + 2:
            res.append(line[:width]); line = line[width:]
        if line:
            res.append(line)
    return res


def ass_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def srt_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_subs(starts, durs, total):
    cues = []
    for i, (key, _) in enumerate(SCENES):
        text = S.SCENES[i]["text"]
        sents = [x.strip() for x in re.split(r"(?<=[。！？])", text) if x.strip()]
        total_chars = sum(len(x) for x in sents)
        bp = WORK / "voice" / f"{i+1:02d}_{key}.bounds.json"
        bounds = None
        if bp.exists():
            try:
                bounds = json.loads(bp.read_text(encoding="utf-8"))
            except Exception:
                bounds = None
        if bounds and len(bounds) == len(sents):
            base = starts[i] + (1.0 if i == 0 else 0.0)
            for j, s in enumerate(sents):
                b0 = base + bounds[j]["offset"]
                sd = bounds[j]["duration"]
                pieces = wrap(s)
                total = sum(len(x) for x in pieces)
                acc = 0
                for k, p in enumerate(pieces):
                    a = b0 + sd * acc / max(1, total)
                    acc += len(p)
                    b = b0 + sd * acc / max(1, total) - 0.03
                    cues.append((a, b, p.replace(" ", "")))
        else:
            t0 = starts[i] + LEAD + (1.0 if i == 0 else 0.0)
            for s in sents:
                pieces = wrap(s)
                sd = durs[i] * len(s) / max(1, total_chars)
                for j, p in enumerate(pieces):
                    a = t0 + sd * j / len(pieces)
                    b = t0 + sd * (j + 1) / len(pieces) - 0.04
                    cues.append((max(t0, a), min(t0 + durs[i], b), p.replace(" ", "")))
                t0 += sd
    ass = WORK / "subs.ass"
    with open(ass, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n"
                "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
                "[V4+ Styles]\n"
                "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
                "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,"
                "BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
                "Style: Default,Noto Serif CJK SC,40,&H00C1E7F6,&H000000FF,&H00101010,"
                "&H80000000,0,0,0,0,100,100,0.4,0,1,1.6,0.6,2,120,120,82,1\n\n"
                "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
        for a, b, p in cues:
            if b <= a:
                continue
            f.write(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Default,,0,0,0,,{p}\n")
    # SRT
    srt = DOCS / "subtitles" / "ISP_Raw_Animated_5min.srt"
    srt.parent.mkdir(exist_ok=True)
    with open(srt, "w", encoding="utf-8") as f:
        n = 0
        for a, b, p in cues:
            if b <= a:
                continue
            n += 1
            f.write(f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{p}\n\n")
    return ass, srt, len(cues)


def decode_mp3(p):
    cmd = [str(FF), "-v", "error", "-i", str(p), "-f", "s16le", "-acodec", "pcm_s16le",
           "-ac", "2", "-ar", "48000", "-"]
    raw = subprocess.check_output(cmd)
    return np.frombuffer(raw, dtype="<i2").reshape(-1, 2)


def build_audio(starts, durs, total):
    chunks = [np.zeros((48000, 2), dtype=np.int16)]
    for i in range(len(SCENES)):
        a = decode_mp3(WORK / "voice" / f"{i+1:02d}_{SCENES[i][0]}.mp3")
        chunks.append(a)
        chunks.append(np.zeros((int(TAIL * 48000), 2), dtype=np.int16))
    data = np.concatenate(chunks, axis=0)
    need = int(total * 48000)
    if len(data) < need:
        data = np.pad(data, ((0, need - len(data)), (0, 0)))
    data = data[:need]
    voice = WORK / "voice.wav"
    with wave.open(str(voice), "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(48000)
        f.writeframes(data.tobytes())
    return voice


def build_music(total):
    sr = 48000
    n = int(total * sr)
    t = np.arange(n) / sr
    out = np.zeros((n, 2), dtype=np.float32)
    # 简单的 Am - F - C - G 氛围铺底
    chords = [(220.00, 261.63, 329.63), (174.61, 220.00, 261.63),
              (261.63, 329.63, 392.00), (196.00, 246.94, 293.66)]
    bar = 8.0
    for k in range(int(total / bar) + 1):
        a, b = k * bar, min(total, (k + 1) * bar)
        tt = t[int(a * sr):int(b * sr)]
        if len(tt) == 0:
            continue
        env = np.minimum(1, tt / 1.8) * np.minimum(1, (b - a - tt) / 2.0)
        env = np.clip(env, 0, 1) ** 1.5
        for f in chords[k % 4]:
            sig = (np.sin(2 * np.pi * f * tt) * 0.5 +
                   np.sin(2 * np.pi * f * 2.01 * tt) * 0.18)
            out[int(a * sr):int(b * sr), 0] += sig * env * 0.018
            out[int(a * sr):int(b * sr), 1] += sig * env * 0.018
    # 稀疏琶音
    for k in range(int(total / 0.75) + 1):
        a = k * 0.75
        if a >= total:
            break
        f = chords[(k // 10) % 4][k % 3] * 2
        tt = np.arange(int(0.7 * sr)) / sr
        sig = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 5) * 0.02
        i = int(a * sr)
        j = min(n, i + len(sig))
        out[i:j, 0] += sig[:j - i]
        out[i:j, 1] += sig[:j - i]
    # 极轻的底噪，避免死寂
    out += np.random.default_rng(3).normal(0, 0.0008, out.shape).astype(np.float32)
    out = np.clip(out, -0.6, 0.6)
    p = WORK / "music.wav"
    with wave.open(str(p), "wb") as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(sr)
        f.writeframes((out * 32767).astype("<i2").tobytes())
    return p


def render(total, start=0.0, limit=None, out=None):
    out = out or (WORK / "silent.mp4")
    cmd = [str(FF), "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "18", "-pix_fmt", "yuv420p", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    n = int(total * FPS)
    if limit:
        n = min(n, int(limit * FPS))
    idx = 0
    starts, durs, total = TIMELINE
    for fi in range(n):
        t = fi / FPS
        # 当前场景
        si = 0
        for i, st in enumerate(starts):
            if t >= st:
                si = i
        st = starts[si]
        lt = t - st
        scene = SCENES[si][1]
        frame = scene(lt, durs[si])
        # 场景淡入淡出
        fade = min(1.0, lt / 0.55, max(0.0, (durs[si] + TAIL - lt) / 0.55))
        if fade < 1.0:
            frame = Image.blend(BG_IMG, frame, max(0.0, fade))
        # 片头片尾
        if t < 1.0:
            frame = Image.blend(BG_IMG, frame, t)
        if t > total - 1.0:
            frame = Image.blend(BG_IMG, frame, max(0.0, (total - t)))
        proc.stdin.write(frame.tobytes())
        idx += 1
        if idx % 240 == 0:
            print(f"  frames {idx}/{n}  ({t:.1f}s)", flush=True)
    proc.stdin.close()
    proc.wait()
    return out


def main():
    global TIMELINE
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", type=float, default=0, help="只渲染前 N 秒")
    ap.add_argument("--skip-render", action="store_true")
    args = ap.parse_args()

    starts, durs, total = build_timeline()
    TIMELINE = (starts, durs, total)
    print("timeline", total, "s", len(SCENES))
    ass, srt, ncues = write_subs(starts, durs, total)
    print("subs", ncues, ass, srt)
    voice = build_audio(starts, durs, total)
    music = build_music(total)
    print("audio", voice, music)

    if args.test:
        out = WORK / "test.mp4"
        render(total, limit=args.test, out=out)
        print("test", out)
        return

    silent = WORK / "silent.mp4"
    if not args.skip_render:
        render(total, out=silent)
    # 混音：人声 -16 LUFS，音乐压到很低的底噪
    mixed = WORK / "mixed.wav"
    subprocess.run([
        str(FF), "-y", "-i", str(voice), "-i", str(music),
        "-filter_complex",
        "[0:a]loudnorm=I=-16:TP=-1.5:LRA=11[v];"
        "[1:a]volume=0.75,lowpass=f=3500[m];"
        "[v][m]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,"
        "alimiter=limit=0.95,afade=t=in:st=0:d=1,"
        f"afade=t=out:st={max(0,total-1.2):.2f}:d=1.2[a]",
        "-map", "[a]", "-ar", "48000", "-ac", "2", str(mixed)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    final = DOCS / "ISP_Raw_Animated_5min.mp4"
    # 烧录字幕 + 混音 + 首尾淡入淡出
    vf = f"ass={ass.name},fade=t=in:st=0:d=1,fade=t=out:st={max(0,total-1.2):.2f}:d=1.2"
    subprocess.run([
        str(FF), "-y", "-i", str(silent), "-i", str(mixed),
        "-vf", vf, "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", str(final)
    ], check=True, cwd=str(WORK), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("DONE", final, audio_duration(final))


if __name__ == "__main__":
    main()
