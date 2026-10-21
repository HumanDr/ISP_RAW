# Stage 17 · Hue/Saturation：色相与饱和度

> **一句话**：在 YUV 里旋转 (U,V)，再缩放饱和度。

## 前后对比

![stage 17](../../docs/images/compare_17.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解色相旋转
- 知道饱和度的含义
- 会看肤色

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 YUV |
| 输出 | f32 YUV，色相/饱和度改变 |
| 目录 | `stages/17_hue_saturation/` |

## 原理

在 YUV 平面里，(U,V) 是一个二维向量：角度是色相，长度是饱和度。旋转角度改色相，缩放长度改饱和度，Y 不变。

公式里 `θ` 是色相旋转角，`sat` 是饱和度。

### 公式

```text
u' = (u cosθ - v sinθ) · sat
v' = (u sinθ + v cosθ) · sat
```

## 代码走读

文件：[`stages/17_hue_saturation/stage.cpp`](stage.cpp)

1. 角度转弧度。
2. 逐像素旋转 + 缩放。
3. U/V clamp [-0.5,0.5]。

## 跑一跑

```bash
./build/isp_17_hue_saturation out/16_nr_chroma.isp out/17_hue_saturation.isp --sat 1.08 --hue 0
```

## 观察与实验

- sat 0.5/1/1.5。
- hue ±30°，看肤色。
- 把 sat 设 0，得到灰度。

## 常见坑

- 旋转后不 clamp，U/V 溢出。
- 只改 R/B 通道，肤色会偏。
- 在 RGB 里改饱和度，容易过曝。

## 为什么放在这个位置

色相/饱和度是最后的颜色创作步骤；放在 YUV 域，Y 不变，肤色/天空可以单独改。

## 自检

- 色相旋转多少度会互补？
- 饱和度 0 会得到什么？
- 为什么在 YUV 里做比 RGB 好？

---

**上一节** → [Stage 16 · NR Chroma](../16_nr_chroma/README.md)  
**下一节** → [Stage 18 · Scale & Crop](../18_scale_crop/README.md)
