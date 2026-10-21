# Stage 06 · Demosaic：去马赛克

> **一句话**：每个像素只有一个颜色，另外两个靠邻居插值。

## 前后对比

![stage 06](../../docs/images/compare_06.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解 Bayer 的采样率
- 知道双线性和 MHC 的差别
- 会看伪彩和拉链纹

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 Bayer |
| 输出 | f32 RGB，三通道 |
| 目录 | `stages/06_demosaic/` |

## 原理

Bayer 上 R/B 各占 25%，G 占 50%。每个像素缺少两个颜色，必须插值。双线性是邻居平均，快，但在黑白边缘会产生拉链纹和伪彩。

Malvar-He-Cutler 用 5×5 卷积，同时利用已知通道的梯度修正未知通道，边缘更干净。代价是计算量更大。

### 公式

```text
G = (G左+G右+G上+G下)/4
MHC：5×5 卷积 + 已知通道梯度修正
```

## 代码走读

文件：[`stages/06_demosaic/stage.cpp`](stage.cpp)

1. `bilinear()` 处理边界和 G 像素的两种方向。
2. MHC 用 4 个卷积核：kG、kRgH、kRgV、kRb。
3. 输出分配新 3 通道 `Image`，`space=RGB`。

## 跑一跑

```bash
./build/isp_06_demosaic out/05_awb.isp out/06_demosaic.isp
./build/isp_06_demosaic out/05_awb.isp out/06_bilinear.isp --method bilinear
```

## 观察与实验

- 100% 裁切对比 bilinear/MHC。
- 找黑白边界，观察伪彩。
- 把 CFA 改错，看颜色错位。

## 常见坑

- 在 Gamma 后去马赛克，插值不再是线性的。
- 只对 R/B 插值，G 不插，边缘会偏绿。
- 边界不 clamp，5×5 卷积会越界。

## 为什么放在这个位置

去马赛克是 RAW 域和 RGB 域的分界：输入单通道 Bayer，输出三通道 RGB。它必须在白平衡之后、颜色校正之前。

## 自检

- 为什么 G 的采样率是 R/B 的两倍？
- 双线性和 MHC 的伪彩差在哪？
- 为什么边界要用双线性兜底？

---

**上一节** → [Stage 05 · AWB](../05_awb/README.md)  
**下一节** → [Stage 07 · NR Color](../07_nr_color/README.md)
