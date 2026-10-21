# Stage 19 · Encoder：输出 PNG / YUV

> **一句话**：YUV→RGB 写 PNG；可选写 YUV420 planar。

## 前后对比

![stage 19](../../docs/images/compare_19.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解 YUV→RGB
- 知道 4:2:0 是什么
- 会检查输出

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 YUV |
| 输出 | 8bit RGB PNG；可选 YUV420 `.yuv` |
| 目录 | `stages/19_encoder/` |

## 原理

显示器和 PNG 要 RGB，所以最后一步把 YUV 转回 RGB：

R=Y+1.5748V，G=Y-0.1873U-0.4681V，B=Y+1.8556U。

`--yuv` 还会写 YUV420：Y 全分辨率，U/V 各 2×2 下采样，文件大小约为 RGB 的一半。

### 公式

```text
R = Y + 1.5748V
G = Y - 0.1873U - 0.4681V
B = Y + 1.8556U
```

## 代码走读

文件：[`stages/19_encoder/stage.cpp`](stage.cpp)

1. 逐像素 YUV→RGB，量化到 8bit。
2. `write_png_rgb8()` 写 PNG。
3. `--yuv` 时写 Y/U/V 三个平面。

## 跑一跑

```bash
./build/isp_19_encoder out/18_scale_crop.isp out/final.png --yuv
```

## 观察与实验

- 看 PNG 和 YUV 的文件大小。
- 用 ffmpeg 读 YUV420，确认格式。
- 对比 `--yuv` 与不写的输出。

## 常见坑

- YUV→RGB 系数和前面 RGB→YUV 不互逆，颜色会偏。
- U/V 没减 0.5 就量化，颜色整体偏。
- YUV420 的宽高不是偶数，平面大小算错。

## 为什么放在这个位置

编码是“数据 → 文件”的边界：之前都是浮点线性/显示数据，最后才量化成 8bit，并可选 4:2:0 压缩色度。

## 自检

- YUV420 的 U/V 为什么只有 1/4 大小？
- 量化误差会出现在哪里？
- PNG 与 YUV 的用途差别？

---

**上一节** → [Stage 18 · Scale & Crop](../18_scale_crop/README.md)  
**下一节** → [课程首页](../../README.md)
