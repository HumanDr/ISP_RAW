# Stage 09 · Color Correction：颜色校正矩阵

> **一句话**：相机 RGB → XYZ → linear sRGB。

## 前后对比

![stage 09](../../docs/images/compare_09.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解 CCM 的作用
- 知道 cam_to_xyz 的方向
- 会看行归一化和负系数

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 RGB，相机色彩空间 |
| 输出 | f32 RGB，linear sRGB |
| 目录 | `stages/09_color_correction/` |

## 原理

相机 RGB 不是 sRGB。不同 CFA 的光谱响应不同，同一块中性灰在相机里可能是 (0.4, 0.5, 0.3)。CCM 把这个“相机色彩空间”映射到 CIE XYZ，再映射到 sRGB。

meta 里的 `cam_to_xyz` 已经包含白平衡后的相机 RGB → XYZ(D65)。本工程再乘 XYZ→sRGB，得到最终矩阵。每行归一化，保证白点不变。

### 公式

```text
M = XYZ_to_sRGB · cam_to_xyz
out = M · rgb
```

## 代码走读

文件：[`stages/09_color_correction/stage.cpp`](stage.cpp)

1. `mat3_mul` 做 3×3 乘法。
2. 每行除以行和，保证 (1,1,1) 仍是白。
3. 逐像素矩阵乘，负值 clamp。

## 跑一跑

```bash
./build/isp_09_color_correction out/08_xtalk.isp out/09_color_correction.isp
```

## 观察与实验

- 把 `cam_to_xyz` 改成单位矩阵，看颜色如何变化。
- 去掉行归一化，观察整体偏色。
- 看矩阵的负系数，解释为什么暗部噪声会被放大。

## 常见坑

- 把矩阵方向弄反（XYZ→相机 vs 相机→XYZ）。
- 在 Gamma 后做 CCM，线性关系不成立。
- 不 clamp 负值，后续 Gamma 会出现 NaN。

## 为什么放在这个位置

CCM 是“相机 RGB → sRGB”的核心线性变换，必须在 Gamma 之前；Gamma 之后数据不再线性，矩阵乘法就不成立。

## 自检

- cam_to_xyz 的方向是哪边到哪边？
- 负系数为什么放大噪声？
- 行归一化的几何意义是什么？

---

**上一节** → [Stage 08 · X-talking](../08_xtalk/README.md)  
**下一节** → [Stage 10 · HDR/WDR](../10_hdr_wdr/README.md)
