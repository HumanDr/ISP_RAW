# Stage 15 · Contrast/Brightness：对比度/亮度

> **一句话**：只改 Y：Y' = (Y-0.5)·contrast + 0.5 + brightness。

## 前后对比

![stage 15](../../docs/images/compare_15.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解线性对比度
- 知道死黑/死白
- 会看直方图

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 YUV |
| 输出 | f32 YUV，Y 对比度/亮度改变 |
| 目录 | `stages/15_contrast_brightness/` |

## 原理

这是显示端的线性对比度/亮度，不改变色度。对比度太大暗部会死黑、亮部会死白；亮度偏移会让整体变亮/变暗。

只改 Y，U/V 不变，所以色相不变。

### 公式

```text
Y' = (Y - 0.5) × contrast + 0.5 + brightness
```

## 代码走读

文件：[`stages/15_contrast_brightness/stage.cpp`](stage.cpp)

1. 逐像素只改 channel 0。
2. clamp 到 [0,1]。
3. 默认 contrast 1.05，brightness 0.005。

## 跑一跑

```bash
./build/isp_15_contrast_brightness out/14_edge_enhance.isp out/15_contrast_brightness.isp --contrast 1.05 --brightness 0.005
```

## 观察与实验

- 对比度 0.8/1.0/1.3。
- 亮度 ±0.05，看直方图。
- 把 contrast 设 2，观察死黑。

## 常见坑

- 对 RGB 三通道做对比度，饱和度会变。
- 在 Gamma 前做，线性关系不同。
- 不 clamp，后面量化会回绕。

## 为什么放在这个位置

对比度/亮度是显示端操作，放在 YUV 域只改 Y，色相不变；放在 RGB 域会让饱和度一起变。

## 自检

- 对比度 2 为什么会死黑？
- brightness 与曝光的关系？
- 为什么只改 Y？

---

**上一节** → [Stage 14 · Edge Enhance](../14_edge_enhance/README.md)  
**下一节** → [Stage 16 · NR Chroma](../16_nr_chroma/README.md)
