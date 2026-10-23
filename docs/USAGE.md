# 使用手册

## 1. 编译

```bash
./build.sh
```

依赖：g++（C++17）、CMake ≥ 3.16、libpng-dev。
Ubuntu：`sudo apt install build-essential cmake libpng-dev`。

产物：`build/isp_00_raw_load ... isp_19_encoder`、`isp_pipeline`、`isp_dump`、`isp_info`。

## 2. 数据格式

### 2.1 `.raw`

- 16bit little-endian；
- 无文件头；
- 单通道 Bayer；
- 大小必须等于 `width * height * 2`。

### 2.2 `.meta`

一行一个字段，`#` 开头是注释：

```text
width 5760
height 3840
bayer RGGB
black 2047 2047 2047 2048
white 15000
wb 1.649 1.000 2.165
cam_to_xyz 0.7385 -0.0108 0.2229 ...
camera Canon EOS 5D Mark III
```

`cam_to_xyz` 是“白平衡后的相机 RGB → XYZ(D65)”矩阵，用于 stage 09 的 CCM。
没有它，颜色只能靠猜。

## 3. 运行

```bash
# 内存流水线（推荐）
./run_pipeline.sh

# 保存每一步 .isp（约 2 GB）
./run_pipeline.sh --keep

# 每个 stage 一个进程
./run_pipeline.sh --steps
```

输出：

- `out/final.png`：2880×1620 RGB；
- `out/stage/*.isp` 或 `out/steps/*.isp`：中间结果；
- `--yuv`：额外写 `out/final.yuv`（YUV420 planar）。

## 4. 单 stage 工具

```bash
./build/isp_00_raw_load     <in.raw> <out.isp> [--meta file.meta]
./build/isp_01_blc          <in.isp> <out.isp> [--noclip]
./build/isp_02_lsc          <in.isp> <out.isp> [--strength 0.7]
./build/isp_03_dpc          <in.isp> <out.isp> [--threshold 0.05]
./build/isp_04_nr_raw       <in.isp> <out.isp> [--sigma 0]
./build/isp_05_awb          <in.isp> <out.isp> [--no-gray-world] [--strength 0.5]
./build/isp_06_demosaic     <in.isp> <out.isp> [--method mhc|bilinear]
./build/isp_07_nr_color     <in.isp> <out.isp> [--strength 0.4]
./build/isp_08_xtalk        <in.isp> <out.isp> [--strength 0.04]
./build/isp_09_color_correction <in.isp> <out.isp> [--no-normalize]
./build/isp_10_hdr_wdr      <in.isp> <out.isp> [--strength 0.4]
./build/isp_11_gamma        <in.isp> <out.isp> [--manual --ev 0]
./build/isp_12_color_space  <in.isp> <out.isp>
./build/isp_13_nr_luma      <in.isp> <out.isp> [--sigma 0.012]
./build/isp_14_edge_enhance <in.isp> <out.isp> [--amount 0.4]
./build/isp_15_contrast_brightness <in.isp> <out.isp> [--contrast 1.05] [--brightness 0.005]
./build/isp_16_nr_chroma    <in.isp> <out.isp> [--strength 0.4]
./build/isp_17_hue_saturation <in.isp> <out.isp> [--hue 0] [--sat 1.08]
./build/isp_18_scale_crop   <in.isp> <out.isp> [--scale 0.5] [--crop]
./build/isp_19_encoder      <in.isp> <out.png> [--yuv]
```

每个工具都会打印统计、CFA/空间、裁剪比例。

## 5. `isp_pipeline` 参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--raw` | `data/sample.raw` | 输入 RAW |
| `--meta` | `data/sample.meta` | 元数据 |
| `--out` | `out/final.png` | 输出 PNG |
| `--work` | `out` | `--keep` 的中间目录 |
| `--keep` | 关 | 保存每个 stage 的 `.isp` |
| `--yuv` | 关 | 额外写 YUV420 |
| `--lsc` | 0.7 | LSC 强度 |
| `--dpc` | 0.05 | 坏点阈值 |
| `--nrraw` | 0（自动） | RAW 降噪 σ |
| `--awb-strength` | 0.5 | 灰度世界与相机参考的混合 |
| `--no-gray-world` | 关 | 只用 meta 的 WB |
| `--method` | `mhc` | 去马赛克 |
| `--xtalk` | 0.04 | 串扰强度 |
| `--wdr` | 0.4 | 高光压缩 |
| `--manual --ev` | 关 | 手动曝光 |
| `--scale` | 0.5 | 缩放（0.5=1/2） |
| `--no-crop` | 关 | 不裁 16:9 |
| `--nr-color` | 0.4 | 色度中值强度 |
| `--nr-luma` | 0.012 | 亮度双边 σ |
| `--edge` | 0.4 | 边缘增强 |
| `--contrast` | 1.05 | 对比度 |
| `--brightness` | 0.005 | 亮度偏移 |
| `--nr-chroma` | 0.4 | 色度中值强度 |
| `--hue` | 0 | 色相旋转 |
| `--sat` | 1.08 | 饱和度 |

## 6. 观察中间结果

```bash
./build/isp_dump out/stage/03_dpc.isp out/03.png
./build/isp_info out/stage/03_dpc.isp
```

`isp_dump` 对 Bayer 输出灰度；对 RGB/YUV 输出彩色（YUV 会自动转 RGB）。

AE/AF 旁路统计：

```bash
./build/isp_ae_af data/sample.raw --meta data/sample.meta
```

它只打印“建议 EV / 对焦清晰度”，不驱动硬件——真实 3A 是闭环。

## 7. 换成自己的 RAW

1. 准备 `your.raw`：16bit LE、无头、Bayer；
2. 复制 `data/sample.meta`，改 `width/height/bayer/black/white/wb/cam_to_xyz`；
3. 运行：

```bash
./build/isp_pipeline --raw your.raw --meta your.meta --out out/your.png
```

如果文件大小不匹配，会有明确报错。

## 8. 性能

本机单线程 5760×3840：

| 阶段 | 耗时 |
|---|---|
| 06 Demosaic | ~1.3 s |
| 07 NR Color | ~3.3 s |
| 16 NR Chroma | ~3.2 s |
| 19 Encoder | ~1.3 s |
| **全流程** | **~13 s** |

峰值内存约 580 MB。中间文件总量约 2 GB。

## 9. 排错

| 现象 | 原因 |
|---|---|
| raw 文件大小不对 | 宽高/位深/字节序和 meta 不一致 |
| 全黑/全白 | black/white 写错 |
| 颜色发绿 | 没跑 stage 09，或 cam_to_xyz 缺失 |
| YUV 预览花屏 | 把 YUV 当 RGB 显示；用 `isp_dump` |
| 输出尺寸不对 | `--scale` / `--no-crop` |
| 编不过 | 缺 libpng-dev |

## 10. 扩展

1. 在 `stages.h` 声明；
2. 新建 `stages/20_xxx/stage.cpp`；
3. 在 `CMakeLists.txt` 加入；
4. 写 `main.cpp`；
5. 在 `isp_pipeline.cpp` 调用；
6. 写 README，跑 `isp_dump` 做对比图。
