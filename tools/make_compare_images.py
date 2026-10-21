#!/usr/bin/env python3
"""为每个 stage 生成“上一阶段 vs 本阶段”的并排图。"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "images"
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "figure.facecolor": "white"})

NAMES = ["RAW 加载", "BLC", "LSC", "BPC/DPC", "NR RAW", "AWB", "Demosaic",
         "NR Color", "X-talking", "Color Correction", "HDR/WDR", "Gamma",
         "Color Space", "NR Luma", "Edge Enhance", "Contrast", "NR Chroma",
         "Hue/Sat", "Scale/Crop", "Encoder"]


def main():
    for i in range(1, 20):
        a = Image.open(IMG / f"stage_{i-1:02d}.png").convert("RGB")
        b = Image.open(IMG / f"stage_{i:02d}.png").convert("RGB")
        fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
        axes[0].imshow(a); axes[0].axis("off")
        axes[0].set_title(f"上一阶段：{i-1:02d} {NAMES[i-1]}", fontsize=11)
        axes[1].imshow(b); axes[1].axis("off")
        axes[1].set_title(f"本阶段：{i:02d} {NAMES[i]}", fontsize=11)
        fig.suptitle(f"Stage {i:02d} 前后对比（同一张 .raw，同一次流水线）", fontsize=14)
        out = IMG / f"compare_{i:02d}.png"
        fig.savefig(out, dpi=140, bbox_inches="tight")
        plt.close(fig)
        print("wrote", out.name)


if __name__ == "__main__":
    main()
