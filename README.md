# 从 .raw 到 RGB：手写 ISP 全流程（C++ 教学工程）

> 这是一门按 **RAW 域 → RGB 域 → YUV 域** 组织的 ISP 实践课。
> 输入是 **无文件头的 16bit `.raw`**（真实相机 Bayer 数据 + `.meta`），
> 输出是 **RGB PNG**（可选 YUV420 `.yuv`）。
> 20 个目录 = 20 节课，每个阶段都能单独编译、单独运行、单独观察。

![final](docs/images/final_full.png)

## 先跑起来

```bash
./build.sh
./run_pipeline.sh
```

输出：`out/final.png`（2880×1620，约 13 秒跑完）。

想一步一步看：

```bash
./run_pipeline.sh --steps     # 20 个 stage 分别跑，中间文件在 out/steps/
./run_pipeline.sh --keep      # 或一次跑完，同时保存 out/stage/*.isp
```

## 输入：为什么是 .raw

纯 `.raw` 只有像素，没有宽高/CFA/黑电平，所以旁边必须有一个 `.meta`：

```text
data/sample.raw    5760×3840，16bit little-endian，RGGB Bayer
data/sample.meta   width/height/bayer/black/white/wb/cam_to_xyz
```

`sample.raw` 来自一张真实的 Canon 5D3 未压缩 DNG，Bayer 数据被原样导出；
来源与许可见 [`data/README.md`](data/README.md)。你可以用 `xxd` 直接看到像素。

## 整条流水线

![pipeline](docs/images/pipeline.png)

| 域 | 阶段 |
|---|---|
| RAW 域 | [00 RAW 加载](stages/00_raw_load/README.md) → [01 BLC 黑电平](stages/01_blc/README.md) → [02 LSC 镜头阴影](stages/02_lsc/README.md) → [03 BPC/DPC 坏点](stages/03_dpc/README.md) → [04 NR RAW](stages/04_nr_raw/README.md) → [05 AWB](stages/05_awb/README.md) → [06 Demosaic](stages/06_demosaic/README.md) |
| RGB 域 | [07 NR Color](stages/07_nr_color/README.md) → [08 X-talking](stages/08_xtalk/README.md) → [09 Color Correction](stages/09_color_correction/README.md) → [10 HDR/WDR](stages/10_hdr_wdr/README.md) → [11 Gamma](stages/11_gamma/README.md) → [12 Color Space](stages/12_color_space/README.md) |
| YUV 域 | [13 NR Luma](stages/13_nr_luma/README.md) → [14 Edge Enhance](stages/14_edge_enhance/README.md) → [15 Contrast/Brightness](stages/15_contrast_brightness/README.md) → [16 NR Chroma](stages/16_nr_chroma/README.md) → [17 Hue/Saturation](stages/17_hue_saturation/README.md) → [18 Scale & Crop](stages/18_scale_crop/README.md) → [19 Encoder](stages/19_encoder/README.md) |

> 旁路：`./build/isp_ae_af data/sample.raw` 会打印 AE 亮度分位数和 AF 绿色梯度。
> 它们是不进图像链路的控制闭环。

一张图看 20 步的变化：

![contact](docs/images/stage_contact.png)

> 前 7 步是灰度，因为数据还是单通道 Bayer；stage 06 之后才是 RGB，
> stage 12 之后进入 YUV。这不是 bug，是 ISP 的三个域。

## 目录结构

```text
ISP_Raw_Course/
├── build.sh / run_pipeline.sh
├── CMakeLists.txt
├── stages/
│   ├── 00_raw_load/{README.md,stage.cpp,main.cpp}
│   ├── 01_blc/
│   └── ... 19_encoder/
├── common/           Image / .raw / .isp / PNG / CLI
├── apps/             isp_pipeline / isp_dump / isp_info
├── data/             sample.raw + sample.meta + README
├── docs/             USAGE / PRINCIPLES / PPT / 视频 / 插图
└── out/              final.png / stage/*.isp
```

## 与旧版 DNG 工程的区别

| 项目 | 旧版 | 本工程 |
|---|---|---|
| 输入 | 未压缩 DNG（含 TIFF 结构） | **纯 .raw + .meta** |
| 阶段 | 11 个 | **20 个，按三域组织** |
| RAW 域 | BLC/LSC/DPC/NR/WB/Demosaic | 同左，命名对齐视频 |
| RGB 域 | CCM/Gamma/Sharpen | **NR Color / X-talking / CCM / HDR/WDR / Gamma / Color Space** |
| YUV 域 | 无 | **NR Luma / Edge / Contrast / NR Chroma / Hue-Sat / Scale-Crop / Encoder** |
| 输出 | 8bit PNG | **PNG + 可选 YUV420** |


## 文档

- [使用手册](docs/USAGE.md)：参数、每个 stage 的命令、.raw/.meta 格式、排错。
- [原理总论](docs/PRINCIPLES.md)：三域流程、BLC/LSC/DPC/去马赛克/CCM/YUV 的原理。
- [PPTX](docs/ISP_Raw_5min.pptx) / [PDF](docs/ISP_Raw_5min.pdf)：10 页，16:9。
- [讲解视频](docs/ISP_Raw_5min.mp4)：5 分 13 秒，1080p，烧录字幕。
- [讲解词](docs/PPT_讲解词.md)：与视频逐句一致，含时间轴。
- 每节目的讲义：见上表。

## 边界

这是教学工程，不是量产 ISP：LSC 用图像统计近似，AWB 是灰度世界 + 参考增益，
X-talking/CCM 用简化矩阵，HDR 只做高光软压缩，没有 3A 闭环、镜头畸变、
色差、多帧降噪、SIMD/GPU。原理文档最后一章会列出“从教学到产品”还缺什么。
