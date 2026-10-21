#!/usr/bin/env python3
"""生成新工程的文档插图：流程图、20 个 stage 预览、联系表、RAW 直方图。"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from isp_io import read_isp

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "axes.unicode_minus": False,
                     "figure.facecolor": "white"})

STAGES = [
    ("00", "RAW 加载", "raw + meta"),
    ("01", "BLC", "黑电平"),
    ("02", "LSC", "镜头阴影"),
    ("03", "BPC/DPC", "坏点"),
    ("04", "NR RAW", "RAW 降噪"),
    ("05", "AWB", "自动白平衡"),
    ("06", "Demosaic", "去马赛克"),
    ("07", "NR Color", "色度降噪"),
    ("08", "X-talking", "串扰校正"),
    ("09", "Color Corr.", "颜色校正"),
    ("10", "HDR/WDR", "高光压缩"),
    ("11", "Gamma", "曝光+Gamma"),
    ("12", "Color Space", "RGB→YUV"),
    ("13", "NR Luma", "亮度降噪"),
    ("14", "Edge Enhance", "边缘增强"),
    ("15", "Contrast", "对比度"),
    ("16", "NR Chroma", "色度降噪"),
    ("17", "Hue/Sat", "色调饱和"),
    ("18", "Scale/Crop", "缩放裁剪"),
    ("19", "Encoder", "PNG/YUV"),
]


def save(fig, name):
    p = OUT / name
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", p.relative_to(ROOT))


def pipeline_diagram():
    rows = [
        ("RAW 域（Bayer，单通道）", STAGES[0:7], "#dbeafe"),
        ("RGB 域（三通道，线性/显示）", STAGES[7:13], "#ffedd5"),
        ("YUV 域（BT.709，Y/U/V）", STAGES[13:20], "#dcfce7"),
    ]
    fig, ax = plt.subplots(figsize=(16, 8.2))
    ax.set_xlim(0, 10.2)
    ax.set_ylim(0.4, 8.6)
    ax.axis("off")
    y0 = [7.0, 4.4, 1.8]
    for (title, sts, color), y in zip(rows, y0):
        ax.text(0.2, y + 0.95, title, fontsize=12, weight="bold", color="#334155")
        n = len(sts)
        for i, (num, name, sub) in enumerate(sts):
            x = 0.35 + i * 1.38
            box = FancyBboxPatch((x, y - 0.38), 1.2, 0.76,
                                 boxstyle="round,pad=0.02,rounding_size=0.07",
                                 facecolor=color, edgecolor="#1e3a8a", linewidth=1.3)
            ax.add_patch(box)
            ax.text(x + 0.6, y + 0.12, f"{num} {name}", ha="center", fontsize=9.2,
                    weight="bold")
            ax.text(x + 0.6, y - 0.17, sub, ha="center", fontsize=7.8, color="#475569")
            if i:
                ax.add_patch(FancyArrowPatch((x - 0.18, y), (x, y),
                                             arrowstyle="-|>", mutation_scale=11,
                                             color="#1e3a8a", linewidth=1.5))
        if len(sts) < 7:
            ax.text(0.35 + len(sts) * 1.38, y, "…", fontsize=18, color="#94a3b8")
    # 行间箭头
    ax.add_patch(FancyArrowPatch((9.9, 6.55), (9.9, 5.2), arrowstyle="-|>",
                                 mutation_scale=14, color="#c2410c", linewidth=2))
    ax.add_patch(FancyArrowPatch((9.9, 3.95), (9.9, 2.55), arrowstyle="-|>",
                                 mutation_scale=14, color="#15803d", linewidth=2))
    ax.text(5.1, 8.3, "RAW ISP 全流程：20 个 stage，按 RAW → RGB → YUV 三域组织",
            ha="center", fontsize=15, weight="bold")
    save(fig, "pipeline.png")


def stage_previews():
    thumbs = []
    for num, _, _ in STAGES:
        if num == "19":
            src = ROOT / "out" / "final.png"
            im = Image.open(src)
        else:
            isp = ROOT / "out" / "stage" / f"{num}_{''.join(c for c in STAGES[int(num)][1].lower() if c.isalnum() or c == '_')}.isp"
            # 目录名不是简单从标题推出来的，直接 glob 该编号
            hits = sorted((ROOT / "out" / "stage").glob(f"{num}_*.isp"))
            if not hits:
                print("missing stage", num); continue
            png = ROOT / "out" / "stage" / f"preview_{num}.png"
            args = [str(ROOT / "build" / "isp_dump"), str(hits[0]), str(png)]
            if int(num) >= 11:
                args.append("--linear")
            subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
            im = Image.open(png)
        im = im.convert("RGB")
        im.thumbnail((900, 900), Image.LANCZOS)
        p = OUT / f"stage_{num}.png"
        im.save(p)
        thumbs.append((f"{num} {STAGES[int(num)][1]}", im))
        print("wrote", p.relative_to(ROOT))

    fig, axes = plt.subplots(5, 4, figsize=(15, 12))
    for ax in axes.ravel(): ax.axis("off")
    for i, (title, im) in enumerate(thumbs):
        ax = axes.ravel()[i]
        ax.imshow(im); ax.set_title(title, fontsize=9); ax.axis("off")
    fig.suptitle("同一张 .raw 走过 20 个 stage", fontsize=15)
    save(fig, "stage_contact.png")


def raw_hist():
    img = read_isp(ROOT / "out" / "stage" / "00_raw_load.isp")
    a = img["arr"][::5, ::5, 0].reshape(-1)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.hist(a, bins=300, range=(0, 16000), color="#3b82f6", alpha=.85, log=True)
    ax.axvline(img["black"][0], color="#111827", ls="--")
    ax.axvline(img["white"], color="#dc2626", ls="--")
    ax.set_xlabel("RAW DN"); ax.set_ylabel("像素数（对数）")
    ax.set_title("sample.raw 的直方图：黑电平 2047 / 白电平 15000")
    ax.grid(alpha=.25)
    save(fig, "raw_histogram.png")


def demosaic_compare():
    base = sorted((ROOT / "out" / "stage").glob("05_*.isp"))[0]
    bil = ROOT / "out" / "stage" / "06_bilinear.isp"
    subprocess.run([str(ROOT / "build" / "isp_06_demosaic"), str(base), str(bil),
                    "--method", "bilinear"], check=True, stdout=subprocess.DEVNULL)
    a = ROOT / "out" / "d_bil.png"; b = ROOT / "out" / "d_mhc.png"
    subprocess.run([str(ROOT / "build" / "isp_dump"), str(bil), str(a)], check=True,
                   stdout=subprocess.DEVNULL)
    subprocess.run([str(ROOT / "build" / "isp_dump"),
                    str(sorted((ROOT / "out" / "stage").glob("06_*.isp"))[0]), str(b)], check=True,
                   stdout=subprocess.DEVNULL)
    ia = Image.open(a).crop((2600, 100, 3800, 1000))
    ib = Image.open(b).crop((2600, 100, 3800, 1000))
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].imshow(ia); axes[0].set_title("双线性"); axes[0].axis("off")
    axes[1].imshow(ib); axes[1].set_title("Malvar-He-Cutler"); axes[1].axis("off")
    fig.suptitle("去马赛克：100% 裁切", fontsize=13)
    save(fig, "demosaic_compare.png")


def final_full():
    im = Image.open(ROOT / "out" / "final.png")
    im.thumbnail((1400, 1400), Image.LANCZOS)
    im.save(OUT / "final_full.png")
    print("wrote", (OUT / "final_full.png").relative_to(ROOT))


def main():
    pipeline_diagram()
    raw_hist()
    stage_previews()
    demosaic_compare()
    final_full()


if __name__ == "__main__":
    main()
