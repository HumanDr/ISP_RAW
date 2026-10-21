# Stage 13 · NR Luma：亮度降噪

> **一句话**：只对 Y 做小半径双边，U/V 不动。

## 前后对比

![stage 13](../../docs/images/compare_13.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解亮度噪声
- 知道 σ 的取舍
- 会看细节损失

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 YUV |
| 输出 | f32 YUV，Y 噪声降低 |
| 目录 | `stages/13_nr_luma/` |

## 原理

Y 同时承载亮度和细节。σ 太大画面会“塑料”，太小噪声还在。

3×3 双边，空间权重中心 1.6、十字 1.0、对角 0.7；值域权重用 LUT。只改 channel 0。

### 公式

```text
w = spatial · exp(-(Y(p)-Y(q))²/2σ²)
```

## 代码走读

文件：[`stages/13_nr_luma/stage.cpp`](stage.cpp)

1. 复制 Y 到临时数组。
2. 3×3 双边，只写回 `p[i*3]`。
3. σ 默认 0.012。

## 跑一跑

```bash
./build/isp_13_nr_luma out/12_color_space.isp out/13_nr_luma.isp --sigma 0.012
```

## 观察与实验

- σ 0/0.02/0.05 对比。
- 看暗部噪声和细节。
- 对比只降 Y 和只降 U/V 的差别。

## 常见坑

- 对 YUV 三个通道一起双边，色度会串。
- σ 太大，边缘变糊。
- 在 Gamma 前做，噪声模型不同。

## 为什么放在这个位置

Y 承载细节，降噪要在“细节”和“噪声”之间取舍；放在 YUV 域，U/V 已经分离，不会把色度一起糊掉。

## 自检

- σ 太大会发生什么？
- 为什么只改 channel 0？
- 双边和普通高斯的差别？

---

**上一节** → [Stage 12 · Color Space](../12_color_space/README.md)  
**下一节** → [Stage 14 · Edge Enhance](../14_edge_enhance/README.md)
