# Stage 14 · Edge Enhance：边缘增强

> **一句话**：只增强 Y，避免彩色描边。

## 前后对比

![stage 14](../../docs/images/compare_14.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解 unsharp mask
- 知道为什么要阈值
- 会看白边/光晕

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 YUV |
| 输出 | f32 YUV，Y 边缘增强 |
| 目录 | `stages/14_edge_enhance/` |

## 原理

对 Y 做 3×3 高斯模糊，取 `detail = Y - blur(Y)`，再 `Y' = Y + amount·detail`。

`|detail| < 0.004` 时不处理，避免放大噪声。只改 Y，所以不会出现彩色描边。

### 公式

```text
Y' = Y + amount · (Y - blur(Y))
```

## 代码走读

文件：[`stages/14_edge_enhance/stage.cpp`](stage.cpp)

1. 可分离 3×3 高斯：先横后纵。
2. 细节小于阈值跳过。
3. 结果 clamp [0,1]。

## 跑一跑

```bash
./build/isp_14_edge_enhance out/13_nr_luma.isp out/14_edge_enhance.isp --amount 0.4
```

## 观察与实验

- amount 0/0.5/1.5 对比白边。
- 看彩色边缘是否出现描边。
- 先降噪再锐化，对比顺序反过来。

## 常见坑

- 对 RGB 三通道分别锐化，彩色边缘会描边。
- amount 太大，白边/光晕明显。
- 不设阈值，噪声被放大。

## 为什么放在这个位置

锐化放在降噪之后：先降噪，避免把噪声放大；只锐化 Y，避免彩色描边。

## 自检

- unsharp mask 的“半径”由什么决定？
- 阈值的作用是什么？
- 为什么不在 RAW 域锐化？

---

**上一节** → [Stage 13 · NR Luma](../13_nr_luma/README.md)  
**下一节** → [Stage 15 · Contrast/Brightness](../15_contrast_brightness/README.md)
