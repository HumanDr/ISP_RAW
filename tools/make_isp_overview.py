#!/usr/bin/env python3
"""通用 ISP 科普动画（不介绍任何具体工程，不依赖 PPT）。"""
import json
import math
import re
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMG = DOCS / "images"
WORK = ROOT / "out" / "overview"
WORK.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "tools"))
import make_animation as A
import isp_overview_script as S

A.S = S
A.WORK = WORK
A.DOCS = DOCS
FPS = 24
TAIL = 0.45
LEAD = 0.15
W, H = 1920, 1080

# ---------------------------------------------------------------- assets
LSTAGE = {i: Image.open(IMG / "landscape" / f"stage_{i:02d}.png").convert("RGB")
          for i in range(19)}
LAND = Image.open(IMG / "landscape" / "final_full.png").convert("RGB")
LAND_RAW = LSTAGE[0]


def vignette(im, strength=0.62):
    a = np.asarray(im, dtype=np.float32) / 255.0
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    f = np.clip(1 - strength * r ** 2, 0.2, 1)[..., None]
    return Image.fromarray(np.clip(a * f * 255, 0, 255).astype(np.uint8))


def flat_look(im):
    out = ImageEnhance.Brightness(im).enhance(0.62)
    out = ImageEnhance.Color(out).enhance(0.35)
    out = ImageEnhance.Contrast(out).enhance(0.65)
    a = np.asarray(out, dtype=np.float32)
    a[..., 1] *= 1.06
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def noisy(im, sigma=10):
    a = np.asarray(im, dtype=np.float32)
    rng = np.random.default_rng(5)
    a = a + rng.normal(0, sigma, a.shape)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def warm(im):
    a = np.asarray(im, dtype=np.float32)
    a[..., 0] *= 1.12
    a[..., 2] *= 0.78
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def mosaic(im, cols=24, rows=14):
    small = im.resize((cols, rows), Image.LANCZOS)
    a = np.asarray(small, dtype=np.float32)
    out = np.zeros_like(a)
    for y in range(rows):
        for x in range(cols):
            if y % 2 == 0 and x % 2 == 0:
                out[y, x, 0] = a[y, x, 0]
            elif y % 2 == 1 and x % 2 == 1:
                out[y, x, 2] = a[y, x, 2]
            else:
                out[y, x, 1] = a[y, x, 1]
    m = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    return m.resize(im.size, Image.NEAREST)


FLAT = LSTAGE[0]
VIGN = LSTAGE[2]
NOISY = LSTAGE[3]
WARM = LSTAGE[4]
BILINEAR = Image.open(IMG / "landscape" / "06_bilinear.png").convert("RGB")
SHARP = LSTAGE[14]
HDR_BEFORE = LSTAGE[9]
HDR_AFTER = LSTAGE[10]
DEMO_AFTER = LSTAGE[6]
DEMO_L = Image.open(IMG / "landscape" / "demosaic_left.png").convert("RGB")
DEMO_R = Image.open(IMG / "landscape" / "demosaic_right.png").convert("RGB")
DEMO_DIFF = Image.open(IMG / "landscape" / "demosaic_diff.png").convert("RGB")
DEMO_ZL = Image.open(IMG / "landscape" / "demosaic_left_zoom.png").convert("RGB")
DEMO_ZR = Image.open(IMG / "landscape" / "demosaic_right_zoom.png").convert("RGB")
DEMO_DZ = Image.open(IMG / "landscape" / "demosaic_diff_zoom.png").convert("RGB")
CCM_BEFORE = LSTAGE[8]
CCM_AFTER = LSTAGE[9]

# YUV
_rgb = np.asarray(LAND.resize((960, 540)), dtype=np.float32) / 255
Y = 0.2126 * _rgb[..., 0] + 0.7152 * _rgb[..., 1] + 0.0722 * _rgb[..., 2]
U = (_rgb[..., 2] - Y) / 1.8556
V = (_rgb[..., 0] - Y) / 1.5748


def chan(a, mode):
    if mode == "Y":
        arr = np.stack([np.clip(a, 0, 1) * 255] * 3, axis=2)
    else:
        lo, hi = np.percentile(a, [2, 98])
        t = np.clip((a - lo) / max(1e-6, hi - lo), 0, 1)
        if mode == "U":
            arr = np.stack([20 + 40 * t, 60 + 140 * t, 130 + 80 * t], axis=2)
        else:
            arr = np.stack([70 + 170 * t, 30 + 110 * t, 50 + 100 * t], axis=2)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


Y_IMG, U_IMG, V_IMG = chan(Y, "Y"), chan(U, "U"), chan(V, "V")


def luma_hist(im, bins=128):
    a = np.asarray(im.convert("L").resize((480, 270)), dtype=np.float32) / 255
    h, _ = np.histogram(a, bins=bins, range=(0, 1))
    h = np.log1p(h).astype(np.float32)
    return h / max(1, h.max())


H_FLAT = luma_hist(FLAT)
H_LAND = luma_hist(LAND)
_raw = np.fromfile(ROOT / "data" / "landscape.raw", dtype="<u2").reshape(2056, 3088)
hist_raw, _ = np.histogram(_raw[::4, ::4], bins=128, range=(0, 4096))
hist_blc, _ = np.histogram(
    np.clip((_raw.astype(np.float32) - 127) / (4000 - 127), 0, 1)[::4, ::4] * 4096,
    bins=128, range=(0, 4096))
hist_raw = np.log1p(hist_raw).astype(np.float32); hist_raw /= max(1, hist_raw.max())
hist_blc = np.log1p(hist_blc).astype(np.float32); hist_blc /= max(1, hist_blc.max())


def bayer_land(size=12, cell=36, reveal=1.0, alpha=255):
    im = LAND.resize((size, size), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32) / 255
    tile = Image.new("RGBA", (size * cell, size * cell), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    for y in range(size):
        for x in range(size):
            k = y * size + x
            if k / (size * size) > reveal:
                continue
            if y % 2 == 0 and x % 2 == 0:
                col, v = (210, 92, 72), a[y, x, 0]
            elif y % 2 == 1 and x % 2 == 1:
                col, v = (92, 132, 205), a[y, x, 2]
            else:
                col, v = (105, 180, 132), a[y, x, 1]
            v = 0.25 + 0.75 * v
            d.rectangle((x * cell, y * cell, (x + 1) * cell, (y + 1) * cell),
                        fill=tuple(int(c * v) for c in col) + (alpha,))
    for i in range(size + 1):
        d.line((i * cell, 0, i * cell, size * cell), fill=(10, 10, 10, 120))
        d.line((0, i * cell, size * cell, i * cell), fill=(10, 10, 10, 120))
    return tile


# ---------------------------------------------------------------- scenes
def title(d, kicker, main, t, dur):
    a = A.alpha_at(t, 0, dur, 0.6)
    A.text(d, (110, 72), kicker, 18, A.GOLD, "sans", alpha=a)
    A.text(d, (110, 102), main, 44, A.CREAM, "serif_b", alpha=a)
    A.line(d, (110, 164, 110 + int(140 * A.smooth(t / 0.9)), 164), A.GOLD, 2, a)


def fig(d, idx, cap, a=130):
    A.text(d, (110, 1032), f"FIG. {idx:02d} — {cap}", 13, A.MUTED, "mono", alpha=a)


def scene_intro(t, dur):
    c = A.BG_IMG.copy(); d = ImageDraw.Draw(c, "RGBA")
    a = A.alpha_at(t, 0, dur, 0.7)
    A.text(d, (110, 130), "IMAGE SIGNAL PROCESSOR", 16, A.GOLD, "mono", alpha=a)
    A.text(d, (110, 168), "ISP：把光变成图像", 66, A.CREAM, "serif_b", alpha=a)
    A.text(d, (112, 252), "Image Signal Processor · 图像信号处理器", 21, A.GOLD, "serif", alpha=a)
    A.text(d, (112, 298), "从光子，到 RAW，再到一张彩色照片", 28, (205, 194, 174), "serif", alpha=a)
    A.line(d, (112, 338, 112 + int(260 * A.smooth(t / 1.2)), 338), A.GOLD, 2, a)

    # 光路：镜头 -> 传感器
    ca = A.smooth((t - 1.5) / 1.5) * a
    for i in range(7):
        x0 = 130 + i * 38
        d.line((x0, 390, 420, 570), fill=tuple(A.GOLD) + (int(70 * ca),), width=1)
    d.ellipse((360, 500, 480, 620), outline=tuple(A.CREAM) + (int(180 * ca),), width=2)
    d.rectangle((420, 548, 600, 642), outline=tuple(A.GOLD) + (int(200 * ca),), width=2)
    A.text(d, (380, 650), "Lens", 15, A.MUTED, "sans", alpha=ca)
    A.text(d, (470, 660), "Sensor", 15, A.MUTED, "sans", alpha=ca)

    ea = A.smooth((t - 3.0) / 2.0) * a
    A.paste_fit(c, LAND, (720, 190, 900, 506), zoom=1.03 - 0.03 * A.smooth(t / 6),
                alpha=int(255 * ea))
    A.text(d, (720, 716), "同一束光，经过 ISP 之后的画面", 16, A.MUTED, "sans", alpha=ea)
    A.text(d, (112, 850), "RAW 不是图片，ISP 才是翻译官。", 22, A.CREAM, "serif", alpha=a)
    fig(d, 0, "FROM PHOTON TO PHOTO", int(110 * a))
    return c


def scene_raw(t, dur):
    c = A.BG_IMG.copy(); d = ImageDraw.Draw(c, "RGBA")
    title(d, "01 / 原始数据", "RAW：传感器的原始语言", t, dur)
    a = A.alpha_at(t, 0, dur, 0.6)

    b = bayer_land(12, 36, reveal=A.smooth((t - 1) / 3), alpha=int(255 * a))
    c.paste(b, (100, 250), b)
    A.text(d, (100, 700), "Bayer 马赛克：每个像素只看一种颜色", 16, A.MUTED, "sans", alpha=a)
    A.text(d, (100, 735), "G 占 50%，R/B 各 25%", 16, A.GOLD, "sans", alpha=a)

    A.text(d, (680, 240), "RAW", 46, A.CREAM, "serif_b", alpha=a)
    rows = [("通道", "1（单通道）"), ("位深", "12 / 14 / 16 bit"), ("状态", "线性，未白平衡"),
            ("元数据", "宽高 / CFA / 黑白电平 / 白平衡"), ("用途", "保留最大后期空间")]
    for i, (k, v) in enumerate(rows):
        ra = A.smooth((t - 2 - i * 0.5) / 0.8) * a
        A.text(d, (680, 320 + i * 58), k, 15, A.GOLD, "sans", alpha=ra)
        A.text(d, (790, 320 + i * 58), v, 15, A.CREAM, "sans", alpha=ra)

    A.paste_fit(c, FLAT, (1260, 230, 520, 292), alpha=int(255 * A.smooth((t - 3) / 2) * a))
    A.text(d, (1260, 550), "RAW 看起来又灰又平", 15, A.MUTED, "sans", alpha=a)
    A.draw_hist(d, (1260, 640, 500, 190), hist_raw, A.MUTED, 1.0, True, int(210 * a))
    A.text(d, (1260, 850), "直方图：信息还在，只是没有展开", 14, A.MUTED, "sans", alpha=a)
    fig(d, 1, "RAW IS NOT AN IMAGE", int(110 * a))
    return c


try:
    _pb = json.loads((WORK / "voice" / "03_pipeline.bounds.json").read_text(encoding="utf-8"))
    PIPE_DOM_STARTS = [_pb[2]["offset"], _pb[3]["offset"], _pb[4]["offset"], _pb[5]["offset"]]
except Exception:
    PIPE_DOM_STARTS = [11.95, 19.79, 27.61, 35.47]


def scene_pipeline(t, dur):
    c = A.BG_IMG.copy(); d = ImageDraw.Draw(c, "RGBA")
    title(d, "02 / 全景", "ISP 的三段旅程", t, dur)
    a = A.alpha_at(t, 0, dur, 0.6)
    lanes = [
        ("RAW 域 · 修数据", ["BLC", "LSC", "DPC", "NR", "AWB", "Demosaic"], 258, (66, 104, 150)),
        ("RGB 域 · 算颜色", ["NR Color", "X-Talk", "CC", "WDR", "Gamma", "YUV"], 486, (150, 108, 62)),
        ("YUV 域 · 修观感", ["NR Luma", "Edge", "Contrast", "NR Chroma", "Hue/Sat Control", "Scale"], 714, (62, 112, 82)),
    ]
    # 与配音逐句对齐：每个域的第一句开始，节点再逐个点亮
    if t < PIPE_DOM_STARTS[0]:
        dom = -1
    elif t < PIPE_DOM_STARTS[1]:
        dom = 0
    elif t < PIPE_DOM_STARTS[2]:
        dom = 1
    elif t < PIPE_DOM_STARTS[3]:
        dom = 2
    else:
        dom = 3
    domain_start = PIPE_DOM_STARTS[:3]
    domain_len = [PIPE_DOM_STARTS[1] - PIPE_DOM_STARTS[0],
                  PIPE_DOM_STARTS[2] - PIPE_DOM_STARTS[1],
                  PIPE_DOM_STARTS[3] - PIPE_DOM_STARTS[2]]
    if dom in (0, 1, 2):
        n_on = min(6, 1 + int((t - domain_start[dom]) / domain_len[dom] * 6))
    else:
        n_on = 6
    idx = 0
    for di, (label, names, y, col) in enumerate(lanes):
        A.text(d, (100, y - 48), label, 16, A.GOLD, "sans", alpha=a)
        for j, name in enumerate(names):
            x = 130 + j * 285
            on = (dom == 3) or (dom == di and j < n_on)
            cur = on
            d.rounded_rectangle((x, y, x + 260, y + 92), radius=6,
                                fill=(18, 20, 24) if not on else (28, 26, 22),
                                outline=(tuple(col) + (100,)) if not cur else (tuple(A.GOLD) + (255,)),
                                width=2 if cur else 1)
            A.text(d, (x + 16, y + 12), f"{idx:02d}", 12, A.GOLD if on else A.DIM, "mono", alpha=a)
            A.text(d, (x + 16, y + 36), name, 18, A.CREAM if on else A.DIM, "serif_b", alpha=a)
            if j:
                d.line((x - 25, y + 46, x - 2, y + 46), fill=tuple(A.MUTED) + (90,), width=1)
            idx += 1
    A.text(d, (130, 870), "RAW → RGB → YUV", 22, A.CREAM, "serif", alpha=a)
    A.text(d, (130, 906), "线性运算在前，Gamma 在后", 15, A.MUTED, "sans", alpha=a)
    if dom == 3:
        A.text(d, (130, 790), "AE / AF / AWB", 20, A.GOLD, "mono", alpha=a)
    fig(d, 2, "THREE DOMAINS", int(110 * a))
    return c


try:
    _rb = json.loads((WORK / "voice" / "04_rawfix.bounds.json").read_text(encoding="utf-8"))
    RAW_STARTS = [0.0] + [_rb[i]["offset"] for i in (2, 3, 4, 5, 6)]
except Exception:
    RAW_STARTS = [0.0, 7.93, 14.49, 19.5, 24.66, 28.79]


def scene_rawfix(t, dur):
    c = A.BG_IMG.copy(); d = ImageDraw.Draw(c, "RGBA")
    title(d, "03 / RAW 域", "先把数据修对", t, dur)
    a = A.alpha_at(t, 0, dur, 0.6)
    bounds = RAW_STARTS + [dur]
    names = ["BLC 黑电平补偿", "LSC 镜头阴影矫正", "DPC 坏点矫正", "NR 降噪", "AWB 白平衡", "Demosaic"]
    k = 0
    for i in range(6):
        if t >= bounds[i]:
            k = i
    im = [LSTAGE[0], LSTAGE[2], LSTAGE[3], LSTAGE[4], LSTAGE[5], LSTAGE[6]][k]
    A.paste_fit(c, im, (100, 220, 760, 500), alpha=int(245 * a))
    A.text(d, (100, 742), names[k], 22, A.CREAM, "serif_b", alpha=a)
    A.text(d, (100, 782), "RAW 域的真实变化（示意）", 15, A.MUTED, "sans", alpha=a)

    rx, ry, rw, rh = 1010, 300, 700, 280
    if k == 0:
        A.draw_hist(d, (rx, ry + 40, 300, 190), hist_raw, A.MUTED, 1.0, True, int(160 * a))
        A.draw_hist(d, (rx + 390, ry + 40, 300, 190), hist_blc, A.GOLD, A.smooth(t / 6), True, int(255 * a))
        A.text(d, (rx + 315, ry + 115), "127 → 0", 17, A.CREAM, "sans", alpha=a)
        A.text(d, (rx, ry - 10), "黑电平偏置 → 0", 19, A.CREAM, "serif", alpha=a)
        A.text(d, (rx, ry + 340), "先减偏置，再乘增益", 15, A.MUTED, "sans", alpha=a)
    elif k == 1:
        for i in range(5):
            rr = 55 + i * 52
            d.arc((rx + rw // 2 - rr, ry + rh // 2 - rr, rx + rw // 2 + rr, ry + rh // 2 + rr),
                  0, 360, fill=tuple(A.GOLD) + (int((55 - i * 8) * a),), width=2)
        A.text(d, (rx, ry - 10), "四角增益 > 1", 19, A.CREAM, "serif", alpha=a)
        A.text(d, (rx, ry + 340), "用 flat-field 把暗角拉平", 15, A.MUTED, "sans", alpha=a)
    elif k == 2:
        A.text(d, (rx, ry - 10), "孤立极值 → 同色中值", 19, A.CREAM, "serif", alpha=a)
        gx, gy, cell = rx + 220, ry + 20, 44
        for yy in range(5):
            for xx in range(5):
                center = xx == 2 and yy == 2
                same = abs(xx - 2) + abs(yy - 2) == 1
                d.rectangle((gx + xx * cell, gy + yy * cell, gx + (xx + 1) * cell, gy + (yy + 1) * cell),
                            fill=(70, 26, 22) if center else ((38, 32, 20) if same else (16, 17, 20)),
                            outline=(A.RED if center else (A.GOLD if same else A.DIM)) + (200,), width=2 if center or same else 1)
        A.text(d, (rx, ry + 340), "坏点不修，去马赛克后会扩散", 15, A.MUTED, "sans", alpha=a)
    elif k == 3:
        A.text(d, (rx, ry - 10), "同色邻居双边滤波", 19, A.CREAM, "serif", alpha=a)
        A.paste_fit(c, NOISY, (rx, ry + 20, 320, 200), alpha=int(235 * a))
        A.paste_fit(c, LSTAGE[4], (rx + 350, ry + 20, 320, 200), alpha=int(235 * a))
        A.text(d, (rx, ry + 232), "降噪前", 13, A.MUTED, "sans", alpha=a)
        A.text(d, (rx + 350, ry + 232), "降噪后", 13, A.GOLD, "sans", alpha=a)
        A.text(d, (rx, ry + 340), "只采样同色像素，不混颜色", 15, A.MUTED, "sans", alpha=a)
    elif k == 4:
        A.text(d, (rx, ry - 10), "白平衡：让中性色回到 R=G=B", 19, A.CREAM, "serif", alpha=a)
        for i, (name, val, col) in enumerate(zip("RGB", [1.42, 1.0, 2.10], [A.RED, A.GREEN, A.BLUE])):
            hh = int(110 * val / 2.2)
            d.rectangle((rx + 140 + i * 100, ry + 230 - hh, rx + 180 + i * 100, ry + 230),
                        fill=tuple(col) + (210,))
            A.text(d, (rx + 160 + i * 100, ry + 248), name, 14, A.MUTED, "mono", alpha=a)
        A.text(d, (rx, ry + 340), "灰度世界 + 光源估计", 15, A.MUTED, "sans", alpha=a)
    else:
        A.text(d, (rx, ry - 10), "单通道 → 三通道", 19, A.CREAM, "serif", alpha=a)
        A.paste_fit(c, LSTAGE[6], (rx + 120, ry + 20, 430, 280), alpha=int(245 * a))
        A.text(d, (rx + 120, ry + 312), "去马赛克后", 13, A.GOLD, "sans", alpha=a)
        A.text(d, (rx, ry + 360), "每个像素缺两个颜色，靠邻居插值", 15, A.MUTED, "sans", alpha=a)

    for i, name in enumerate(names):
        xx = 100 + i * 290
        on = i <= k
        d.line((xx, 850, xx + 255, 850), fill=tuple(A.GOLD if on else A.DIM) + (160,), width=3 if on else 1)
        A.text(d, (xx, 866), name, 12, A.CREAM if on else A.MUTED, "sans", alpha=a)
    fig(d, 3, "REPAIRING RAW", int(110 * a))
    return c


def scene_demosaic(t, dur):
    c = A.BG_IMG.copy(); d = ImageDraw.Draw(c, "RGBA")
    title(d, "04 / 去马赛克", "猜出缺失的两个颜色", t, dur)
    a = A.alpha_at(t, 0, dur, 0.6)
    b = bayer_land(10, 42, reveal=A.smooth((t - 0.5) / 3), alpha=int(255 * a))
    c.paste(b, (130, 240), b)
    A.text(d, (130, 690), "Bayer 输入", 15, A.MUTED, "sans", alpha=a)
    A.paste_fit(c, DEMO_AFTER, (700, 220, 520, 360), alpha=int(255 * A.smooth((t - 3) / 2) * a))
    A.text(d, (700, 596), "去马赛克之后", 15, A.MUTED, "sans", alpha=a)
    # 对比：bilinear vs sharp
    if t > 8.2:
        fade = A.smooth((t - 8.2) / 1.2) * a
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rectangle((0, 0, W, H), fill=(5, 6, 9, int(244 * fade)))
        c = c.convert("RGBA"); c.alpha_composite(ov); c = c.convert("RGB"); d = ImageDraw.Draw(c, "RGBA")
        title(d, "04 / 去马赛克", "猜出缺失的两个颜色", t, dur)
        A.text(d, (105, 200), "同一区域，100% 裁剪；红色圆圈放大", 21, A.CREAM, "serif", alpha=fade)
        # 上方两张全图，同样大小
        for i, (im, label) in enumerate([(DEMO_L, "双线性"), (DEMO_R, "Malvar-He-Cutler")]):
            x = 100 + i * 580
            c.paste(im.resize((540, 386), Image.LANCZOS), (x, 245))
            A.text(d, (x, 642), label, 16, A.MUTED if i == 0 else A.GOLD, "sans", alpha=fade)
            d.ellipse((x + 85 - 38, 245 + 200 - 38, x + 85 + 38, 245 + 200 + 38),
                      outline=tuple(A.RED) + (int(230 * fade),), width=3)
        # 下方放大：双线性 / MHC / 逐像素差异
        for i, (im, label, col) in enumerate([(DEMO_ZL, "双线性 ×3", A.MUTED),
                                               (DEMO_ZR, "MHC ×3", A.GOLD),
                                               (DEMO_DZ, "差异 ×18", A.RED)]):
            x = 100 + i * 360
            c.paste(im.resize((320, 240), Image.LANCZOS), (x, 665))
            A.text(d, (x, 910), label, 13, col, "sans", alpha=fade)
        # 右侧解释
        A.text(d, (1235, 250), "第三张不是算法，是逐像素 RGB 差", 18, A.CREAM, "serif", alpha=fade)
        A.text(d, (1235, 292), "|双线性 - MHC|，越亮差越大", 15, A.MUTED, "sans", alpha=fade)
        A.text(d, (1235, 340), "为什么会差：", 16, A.GOLD, "sans", alpha=fade)
        A.text(d, (1235, 375), "双线性对 R/G/B 各自独立做邻居平均；", 14, A.MUTED, "sans", alpha=fade)
        A.text(d, (1235, 405), "在树枝 / 屋顶边缘，三个通道对不齐，", 14, A.MUTED, "sans", alpha=fade)
        A.text(d, (1235, 435), "于是出现彩色边和拉链纹。", 14, A.MUTED, "sans", alpha=fade)
        A.text(d, (1235, 480), "MHC 用 5×5 卷积，沿梯度修正，", 14, A.MUTED, "sans", alpha=fade)
        A.text(d, (1235, 510), "缺失通道跟着边缘走，差得更少。", 14, A.MUTED, "sans", alpha=fade)
        for k in range(220):
            v = int(255 * k / 219)
            d.line((1235 + k, 575, 1235 + k, 590), fill=(v, int(v * 0.6), int(v * 0.22), int(255 * fade)))
        A.text(d, (1235, 598), "相同", 12, A.MUTED, "sans", alpha=fade)
        A.text(d, (1400, 598), "差大", 12, A.MUTED, "sans", alpha=fade)
        A.text(d, (1235, 650), "红色圆圈位置：圈内是同一块树枝/屋顶边缘", 13, A.GOLD, "sans", alpha=fade)
    fig(d, 4, "DEMOSAIC: GUESSING COLOR", int(110 * a))
    return c


def scene_rgb(t, dur):
    c = A.BG_IMG.copy(); d = ImageDraw.Draw(c, "RGBA")
    title(d, "05 / RGB 域", "把颜色算对", t, dur)
    a = A.alpha_at(t, 0, dur, 0.6)
    if t < 6.2:
        A.paste_fit(c, LSTAGE[7], (110, 220, 740, 500), alpha=int(240 * a))
        A.paste_fit(c, LSTAGE[8], (900, 220, 740, 500), alpha=int(240 * a))
        A.text(d, (110, 736), "彩色噪点", 16, A.MUTED, "sans", alpha=a)
        A.text(d, (900, 736), "彩色降噪后", 16, A.GOLD, "sans", alpha=a)
        A.text(d, (110, 800), "先压彩色噪声，不糊亮度", 18, A.CREAM, "serif", alpha=a)
    elif t < 10.4:
        A.paste_fit(c, LSTAGE[8], (110, 220, 740, 500), alpha=int(240 * a))
        A.paste_fit(c, LSTAGE[9], (900, 220, 740, 500), alpha=int(240 * a))
        A.text(d, (110, 736), "串扰 / 偏色", 16, A.MUTED, "sans", alpha=a)
        A.text(d, (900, 736), "串扰校正后", 16, A.GOLD, "sans", alpha=a)
        A.text(d, (110, 800), "补偿滤光片之间漏进来的颜色", 18, A.CREAM, "serif", alpha=a)
    elif t < 17.3:
        A.paste_fit(c, LSTAGE[8], (110, 220, 740, 500), alpha=int(240 * a))
        A.paste_fit(c, LSTAGE[9], (900, 220, 740, 500), alpha=int(240 * a))
        A.text(d, (110, 736), "颜色校正前：偏暖", 16, A.MUTED, "sans", alpha=a)
        A.text(d, (900, 736), "颜色校正后", 16, A.GOLD, "sans", alpha=a)
        A.draw_matrix(d, 110, 800, [1.42, -0.28, 0.06, -0.15, 1.34, -0.09, 0.02, -0.31, 1.39], 48, int(220 * a))
        A.text(d, (110, 980), "相机 RGB → XYZ → linear sRGB", 15, A.MUTED, "sans", alpha=a)
    elif t < 22.4:
        A.paste_fit(c, HDR_BEFORE, (110, 220, 740, 500), alpha=int(240 * a))
        A.paste_fit(c, HDR_AFTER, (900, 220, 740, 500), alpha=int(240 * a))
        A.text(d, (110, 736), "高光硬切：细节丢失", 16, A.MUTED, "sans", alpha=a)
        A.text(d, (900, 736), "高光压缩：保留层次", 16, A.GOLD, "sans", alpha=a)
        A.text(d, (110, 800), "只压 >1 的高光，0..1 不动", 18, A.CREAM, "serif", alpha=a)
    elif t < 27.3:
        A.paste_fit(c, LSTAGE[11], (110, 220, 720, 480), alpha=int(240 * a))
        A.text(d, (110, 730), "Gamma 校正：自动曝光 + sRGB", 16, A.GOLD, "sans", alpha=a)
        A.draw_gamma(d, 930, 290, 640, 350, A.smooth((t - 21) / 5), int(255 * a))
        A.text(d, (930, 700), "线性光不能直接写 8bit", 16, A.MUTED, "sans", alpha=a)
    elif t < 31.7:
        for i, (im, name, col) in enumerate([(Y_IMG, "Y 亮度", A.GREEN), (U_IMG, "U 色度", A.BLUE), (V_IMG, "V 色度", A.RED)]):
            xx = 140 + i * 570
            A.paste_fit(c, im, (xx, 240, 450, 300), alpha=int(245 * a))
            A.text(d, (xx, 560), name, 17, col, "sans", alpha=a)
        A.text(d, (140, 650), "RGB → YUV（BT.709）", 24, A.CREAM, "serif", alpha=a)
        A.text(d, (140, 696), "Y 保留细节，U/V 可以降分辨率", 15, A.MUTED, "sans", alpha=a)
    else:
        A.paste_fit(c, LSTAGE[8], (110, 220, 740, 500), alpha=int(240 * a))
        A.paste_fit(c, LSTAGE[9], (900, 220, 740, 500), alpha=int(240 * a))
        A.text(d, (110, 736), "颜色校正前", 16, A.MUTED, "sans", alpha=a)
        A.text(d, (900, 736), "颜色校正后", 16, A.GOLD, "sans", alpha=a)
        A.text(d, (110, 800), "负系数会放大暗部噪声", 18, A.CREAM, "serif", alpha=a)
    fig(d, 5, "COLOR, DYNAMIC RANGE, GAMMA", int(110 * a))
    return c


def scene_yuv(t, dur):
    c = A.BG_IMG.copy(); d = ImageDraw.Draw(c, "RGBA")
    title(d, "06 / YUV 域", "按人眼的方式修", t, dur)
    a = A.alpha_at(t, 0, dur, 0.6)
    for i, (im, name, col) in enumerate([(Y_IMG, "Y", A.GREEN), (U_IMG, "U", A.BLUE), (V_IMG, "V", A.RED)]):
        xx = 110 + i * 240
        A.paste_fit(c, im, (xx, 240, 220, 150), alpha=int(235 * a))
        A.text(d, (xx, 406), name, 15, col, "mono", alpha=a)
    if t < 8.2:
        A.text(d, (880, 250), "YUV", 52, A.CREAM, "serif_b", alpha=a)
        A.text(d, (880, 322), "亮度 + 两个色度", 22, A.MUTED, "serif", alpha=a)
        A.text(d, (880, 378), "人眼对色度分辨率不敏感", 16, A.MUTED, "sans", alpha=a)
    elif t < 14.6:
        A.paste_fit(c, LSTAGE[13], (900, 230, 380, 250), alpha=int(240 * a))
        A.paste_fit(c, LSTAGE[14], (1320, 230, 380, 250), alpha=int(240 * a))
        A.text(d, (900, 500), "Y 降噪", 15, A.MUTED, "sans", alpha=a)
        A.text(d, (1320, 500), "+ 边缘增强", 15, A.GOLD, "sans", alpha=a)
        A.text(d, (900, 570), "只改 Y，U/V 不动", 20, A.CREAM, "serif", alpha=a)
    elif t < 19.2:
        A.draw_hue_wheel(d, 1200, 430, 170, t * 0.6, int(255 * a))
        A.text(d, (900, 250), "对比度 / 色相 / 饱和度", 22, A.CREAM, "serif", alpha=a)
        A.text(d, (900, 292), "在 YUV 平面里旋转、缩放", 15, A.MUTED, "sans", alpha=a)
        A.text(d, (900, 620), "Y 不变，颜色更自由", 18, A.CREAM, "serif", alpha=a)
    elif t < 26.2:
        A.paste_fit(c, LSTAGE[16], (900, 230, 520, 330), alpha=int(240 * a))
        A.text(d, (900, 590), "420：U/V 各降一半分辨率", 19, A.GOLD, "sans", alpha=a)
        A.text(d, (900, 630), "人眼几乎看不出来", 16, A.MUTED, "sans", alpha=a)
    else:
        A.paste_fit(c, LAND, (900, 230, 420, 280), alpha=int(245 * a))
        A.text(d, (900, 540), "输出 YUV", 22, A.CREAM, "serif", alpha=a)
        A.text(d, (900, 582), "编码器更喜欢 YUV420", 15, A.MUTED, "sans", alpha=a)
        A.text(d, (900, 640), "同样画面，文件更小", 16, A.GOLD, "sans", alpha=a)
    fig(d, 6, "THE HUMAN-VISION DOMAIN", int(110 * a))
    return c


def scene_threea(t, dur):
    c = A.BG_IMG.copy(); d = ImageDraw.Draw(c, "RGBA")
    title(d, "07 / 控制闭环", "3A：测量、反馈、再采集", t, dur)
    a = A.alpha_at(t, 0, dur, 0.6)
    d.rounded_rectangle((760, 410, 1160, 610), radius=12, fill=(22, 24, 28),
                        outline=tuple(A.GOLD) + (220,), width=2)
    A.text(d, (960, 470), "ISP", 36, A.CREAM, "serif_b", anchor="mm", alpha=a)
    A.text(d, (960, 525), "统计 + 处理", 14, A.MUTED, "sans", anchor="mm", alpha=a)
    A.text(d, (330, 470), "Lens / Sensor", 20, A.CREAM, "serif", anchor="mm", alpha=a)
    d.rectangle((260, 350, 560, 590), outline=tuple(A.MUTED) + (160,), width=2)
    A.text(d, (410, 620), "光 → 电荷 → 数字", 14, A.MUTED, "sans", anchor="mm", alpha=a)
    boxes = [("AE", "自动曝光", 1230, 230), ("AF", "自动对焦", 1230, 420), ("AWB", "自动白平衡", 1230, 610)]
    for name, desc, x, y in boxes:
        d.rounded_rectangle((x, y, x + 300, y + 120), radius=8, fill=(20, 22, 26),
                            outline=tuple(A.GOLD) + (160,), width=1)
        A.text(d, (x + 24, y + 20), name, 24, A.GOLD, "mono", alpha=a)
        A.text(d, (x + 24, y + 60), desc, 15, A.CREAM, "sans", alpha=a)
    pulse = 0.5 + 0.5 * math.sin(t * 2.5)
    for y in [290, 480, 670]:
        d.line((560, 470, 760, 470), fill=tuple(A.MUTED) + (120,), width=1)
        d.line((1160, 470, 1230, y), fill=tuple(A.GOLD) + (int(80 + 60 * pulse),), width=2)
        d.ellipse((740, 462, 756, 478), fill=tuple(A.GOLD) + (int(180 + 60 * pulse),))
    A.text(d, (250, 760), "统计直方图 / 对比度 / 颜色分布 → 反馈给镜头和传感器", 18, A.CREAM, "serif", alpha=a)
    A.text(d, (250, 800), "3A 不是滤镜，是闭环控制。", 16, A.MUTED, "sans", alpha=a)
    fig(d, 7, "MEASURE, FEED BACK, CAPTURE AGAIN", int(110 * a))
    return c


def scene_order(t, dur):
    c = A.BG_IMG.copy(); d = ImageDraw.Draw(c, "RGBA")
    title(d, "08 / 顺序", "为什么顺序不能乱", t, dur)
    a = A.alpha_at(t, 0, dur, 0.6)
    left = ["黑电平", "白平衡", "去马赛克", "Gamma"]
    right = ["黑电平", "白平衡", "去马赛克", "Gamma"]
    for i, (x, label) in enumerate([(250, "错误顺序"), (1030, "正确顺序")]):
        A.text(d, (x, 250), label, 22, A.GOLD if i else A.RED, "serif_b", alpha=a)
        seq = [("Gamma", "先做 Gamma"), ("白平衡", "再乘增益"), ("黑电平", "最后减偏置")] if i == 0 else \
              [("黑电平", "先减偏置"), ("白平衡", "再乘增益"), ("Gamma", "最后编码")]
        for j, (name, desc) in enumerate(seq):
            yy = 330 + j * 150
            d.rounded_rectangle((x, yy, x + 430, yy + 95), radius=8, fill=(18, 20, 24),
                                outline=tuple(A.MUTED) + (120,), width=1)
            A.text(d, (x + 20, yy + 15), name, 21, A.CREAM, "serif_b", alpha=a)
            A.text(d, (x + 20, yy + 52), desc, 13, A.MUTED, "sans", alpha=a)
            if j < 2:
                d.line((x + 215, yy + 100, x + 215, yy + 145), fill=tuple(A.GOLD) + (180,), width=2)
    A.text(d, (250, 820), "加性在前，乘性在后；Gamma 永远最后。", 20, A.CREAM, "serif", alpha=a)
    A.text(d, (250, 860), "顺序错了，颜色、噪声和细节会悄悄变差。", 15, A.MUTED, "sans", alpha=a)
    fig(d, 8, "ORDER MATTERS", int(110 * a))
    return c


def scene_apps(t, dur):
    c = A.BG_IMG.copy(); d = ImageDraw.Draw(c, "RGBA")
    title(d, "09 / 应用", "ISP 在哪里", t, dur)
    a = A.alpha_at(t, 0, dur, 0.6)
    cards = [("手机", "小体积 · 低功耗"), ("汽车", "高动态 · 可靠性"),
             ("安防", "日夜 · 低照度"), ("医疗 / 机器视觉", "色彩准确 · 低延迟")]
    for i, (name, desc) in enumerate(cards):
        x = 110 + (i % 2) * 470
        y = 230 + (i // 2) * 210
        d.rounded_rectangle((x, y, x + 420, y + 165), radius=10,
                            fill=(18, 20, 24), outline=tuple(A.GOLD) + (110,), width=1)
        A.text(d, (x + 24, y + 28), name, 24, A.CREAM, "serif_b", alpha=a)
        A.text(d, (x + 24, y + 78), desc, 15, A.MUTED, "sans", alpha=a)
    A.paste_fit(c, LAND, (1100, 230, 680, 382), alpha=int(245 * a))
    A.text(d, (1100, 630), "同一颗传感器，不同的 ISP，能拍出不同的风格。", 16, A.MUTED, "sans", alpha=a)
    A.text(d, (110, 720), "RAW 修数据，RGB 算颜色，YUV 修观感。", 24, A.CREAM, "serif", alpha=a)
    A.text(d, (110, 770), "这，就是 ISP。", 30, A.GOLD, "serif_b", alpha=a)
    fig(d, 9, "ONE SENSOR, MANY LOOKS", int(110 * a))
    return c


SCENES = [("intro", scene_intro), ("raw", scene_raw), ("pipeline", scene_pipeline),
          ("rawfix", scene_rawfix), ("demosaic", scene_demosaic), ("rgb", scene_rgb),
          ("yuv", scene_yuv), ("threea", scene_threea), ("order", scene_order),
          ("apps", scene_apps)]
A.SCENES = SCENES


def write_subs(starts, durs):
    cues = []
    for i, (key, _) in enumerate(SCENES):
        text = S.SCENES[i]["text"]
        sents = [x.strip() for x in re.split(r"(?<=[。！？])", text) if x.strip()]
        bp = WORK / "voice" / f"{i+1:02d}_{key}.bounds.json"
        bounds = None
        if bp.exists():
            try:
                bounds = json.loads(bp.read_text(encoding="utf-8"))
            except Exception:
                bounds = None
        if bounds and len(bounds) == len(sents):
            base = starts[i] + (2.0 if i == 0 else 0.0)
            for j, s in enumerate(sents):
                b0 = base + bounds[j]["offset"]
                dur = bounds[j]["duration"]
                pieces = A.wrap(s, 46)
                total = sum(len(x) for x in pieces)
                acc = 0
                for k, p in enumerate(pieces):
                    a = b0 + dur * acc / max(1, total)
                    acc += len(p)
                    b = b0 + dur * acc / max(1, total) - 0.03
                    cues.append((a, b, p))
        else:
            total = sum(len(x) for x in sents)
            t0 = starts[i] + LEAD + (2.0 if i == 0 else 0.0)
            for s in sents:
                pieces = A.wrap(s, 46)
                sd = durs[i] * len(s) / max(1, total)
                for j, p in enumerate(pieces):
                    a = t0 + sd * j / len(pieces)
                    b = t0 + sd * (j + 1) / len(pieces) - 0.04
                    cues.append((a, b, p))
                t0 += sd
    ass = WORK / "subs.ass"
    with open(ass, "w", encoding="utf-8") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n"
                "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
                "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
                "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
                "Alignment,MarginL,MarginR,MarginV,Encoding\n"
                "Style: Default,Noto Serif CJK SC,36,&H00C1E7F6,&H000000FF,&H00101010,&H80000000,"
                "0,0,0,0,100,100,0.4,0,1,1.6,0.6,2,120,120,82,1\n\n[Events]\n"
                "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
        for a, b, p in cues:
            if b > a:
                f.write(f"Dialogue: 0,{A.ass_time(a)},{A.ass_time(b)},Default,,0,0,0,,{p}\n")
    srt = DOCS / "subtitles" / "ISP_Overview_Animated.srt"
    srt.parent.mkdir(exist_ok=True)
    with open(srt, "w", encoding="utf-8") as f:
        n = 0
        for a, b, p in cues:
            if b <= a: continue
            n += 1
            f.write(f"{n}\n{A.srt_time(a)} --> {A.srt_time(b)}\n{p}\n\n")
    return ass, srt, len(cues)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--reburn", action="store_true")
    args = ap.parse_args()
    starts, durs, total = A.build_timeline()
    durs[0] += 2.0
    total += 2.0
    starts = [0.0]
    for d in durs[:-1]:
        starts.append(starts[-1] + d + A.TAIL)
    A.TIMELINE = (starts, durs, total)
    print("timeline", total, len(SCENES))
    ass, srt, n = write_subs(starts, durs)
    print("subs", n, ass, srt)
    voice = A.build_audio(starts, durs, total, lead=2.0)
    music = A.build_music(total)
    silent = WORK / "silent.mp4"
    if not args.reburn:
        A.render(total, out=silent)
    mixed = WORK / "mixed.wav"
    import subprocess
    subprocess.run([str(A.FF), "-y", "-i", str(voice), "-i", str(music),
                    "-filter_complex",
                    "[0:a]loudnorm=I=-16:TP=-1.5:LRA=11[v];"
                    "[1:a]volume=0.75,lowpass=f=3500[m];"
                    "[v][m]amix=inputs=2:duration=first:dropout_transition=2:normalize=0,"
                    "alimiter=limit=0.95,afade=t=in:st=0:d=1,"
                    f"afade=t=out:st={max(0,total-1.2):.2f}:d=1.2[a]",
                    "-map", "[a]", "-ar", "48000", "-ac", "2", str(mixed)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    final = DOCS / "ISP_Overview_Animated.mp4"
    vf = f"ass={ass.name},fade=t=in:st=0:d=1,fade=t=out:st={max(0,total-1.2):.2f}:d=1.2"
    subprocess.run([str(A.FF), "-y", "-i", str(silent), "-i", str(mixed),
                    "-vf", vf, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", str(final)],
                   check=True, cwd=str(WORK), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("DONE", final, A.audio_duration(final))


if __name__ == "__main__":
    main()
