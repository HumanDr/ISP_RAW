# Stage 16 · NR Chroma：色度降噪

> **一句话**：U/V 的 3×3 中值，比亮度更激进。

## 前后对比

![stage 16](../../docs/images/compare_16.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解色度噪声
- 知道中值的优缺点
- 会看颜色渗色

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 YUV |
| 输出 | f32 YUV，U/V 噪声降低 |
| 目录 | `stages/16_nr_chroma/` |

## 原理

人眼对色度空间分辨率低，所以 U/V 可以做强降噪。中值能去掉孤立彩色噪点，但会让颜色边界轻微渗色。

对 U/V 各做 3×3 中值，按 `strength` 混合。Y 不动。

### 公式

```text
U' = median(U 3×3), V' = median(V 3×3)
U = (1-s)U + sU'
```

## 代码走读

文件：[`stages/16_nr_chroma/stage.cpp`](stage.cpp)

1. 分别复制 U/V。
2. 对每个像素排序 9 个数取中间。
3. 按 strength 混合，写回 channel 1/2。

## 跑一跑

```bash
./build/isp_16_nr_chroma out/15_contrast_brightness.isp out/16_nr_chroma.isp --strength 0.4
```

## 观察与实验

- 强度 0/0.5/1。
- 看彩色噪点和颜色边缘。
- 和 stage 07 对比：一个在 RGB 域，一个在 YUV 域。

## 常见坑

- 中值窗口太大，颜色边界渗色。
- 对 Y 也做中值，细节丢失。
- 强度 1，肤色变成色块。

## 为什么放在这个位置

色度降噪放在亮度处理之后：此时 Y 已经稳定，U/V 可以更激进地中值，不会影响亮度细节。

## 自检

- 中值窗口为什么是 3×3？
- 强度 1 为什么会渗色？
- 和 stage 07 的区别？

---

**上一节** → [Stage 15 · Contrast/Brightness](../15_contrast_brightness/README.md)  
**下一节** → [Stage 17 · Hue/Saturation](../17_hue_saturation/README.md)
