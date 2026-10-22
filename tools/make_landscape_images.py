#!/usr/bin/env python3
"""生成风景示例的 stage 预览和前后对比图（不覆盖旧的水龙头图）。"""
import subprocess
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "out" / "landscape" / "stage"
OUT = ROOT / "docs" / "images" / "landscape"
OUT.mkdir(parents=True, exist_ok=True)
FF = ROOT / "build" / "isp_dump"
NAMES = ["RAW 加载", "BLC", "LSC", "BPC/DPC", "NR RAW", "AWB", "Demosaic",
         "NR Color", "X-Talking", "Color Correction", "HDR/WDR", "Gamma",
         "Color Space", "NR Luma", "Edge Enhance", "Contrast", "NR Chroma",
         "Hue/Sat", "Scale/Crop", "Encoder"]
plt.rcParams.update({"font.family": "Noto Sans CJK JP", "figure.facecolor": "white"})

def main():
    for i in range(19):
        isp = next(SRC.glob(f"{i:02d}_*.isp"))
        png = OUT / f"stage_{i:02d}.png"
        args = [str(FF), str(isp), str(png)]
        if i >= 11:
            args.append("--linear")
        subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
        im = Image.open(png); im.thumbnail((900, 900), Image.LANCZOS); im.save(png)
        print("stage", i)
    final = Image.open(ROOT / "out" / "landscape" / "final.png")
    final.thumbnail((1440, 1440), Image.LANCZOS)
    final.save(OUT / "final_full.png")
    for i in range(1, 20):
        a = Image.open(OUT / f"stage_{i-1:02d}.png").convert("RGB")
        b = Image.open(OUT / f"stage_{i:02d}.png").convert("RGB") if i < 19 else final.convert("RGB")
        fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
        axes[0].imshow(a); axes[0].axis("off"); axes[0].set_title(f"上一阶段：{i-1:02d} {NAMES[i-1]}", fontsize=11)
        axes[1].imshow(b); axes[1].axis("off"); axes[1].set_title(f"本阶段：{i:02d} {NAMES[i]}", fontsize=11)
        fig.suptitle(f"Stage {i:02d} 前后对比（风景 RAW）", fontsize=14)
        fig.savefig(OUT / f"compare_{i:02d}.png", dpi=140, bbox_inches="tight")
        plt.close(fig)
    # demosaic compare: stage 05 awb -> bilinear vs mhc
    base = next(SRC.glob("05_*.isp"))
    bil = ROOT / "out" / "landscape" / "06_bilinear.isp"
    subprocess.run([str(ROOT/"build"/"isp_06_demosaic"), str(base), str(bil), "--method", "bilinear"], check=True, stdout=subprocess.DEVNULL)
    pb = ROOT/"out"/"landscape"/"06_bilinear.png"; pm = ROOT/"out"/"landscape"/"06_mhc.png"
    subprocess.run([str(FF), str(bil), str(pb)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([str(FF), str(SRC/"06_demosaic.isp"), str(pm)], check=True, stdout=subprocess.DEVNULL)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].imshow(Image.open(pb).crop((900, 500, 2100, 1500))); axes[0].set_title("双线性"); axes[0].axis("off")
    axes[1].imshow(Image.open(pm).crop((900, 500, 2100, 1500))); axes[1].set_title("Malvar-He-Cutler"); axes[1].axis("off")
    fig.suptitle("去马赛克：100% 裁切（风景 RAW）", fontsize=13)
    fig.savefig(OUT / "demosaic_compare.png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    print("done")

if __name__ == "__main__":
    main()
