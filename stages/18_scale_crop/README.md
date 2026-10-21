# Stage 18 · Scale & Crop：缩放裁剪

> **一句话**：最后再缩放，避免中间阶段反复重采样。

## 前后对比

![stage 18](../../docs/images/compare_18.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解重采样顺序
- 知道 box 平均
- 会看裁剪构图

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 YUV 全分辨率 |
| 输出 | f32 YUV，1/2 或 1/4 + 可选 16:9 |
| 目录 | `stages/18_scale_crop/` |

## 原理

缩放放在最后，避免中间阶段反复重采样。支持 1/2、1/4 整数倍 box 平均：每个输出像素取 2×2/4×4 输入的平均。

`--crop` 会中心裁成 16:9：宽不变，高取 `w*9/16`。

### 公式

```text
out(x,y) = mean(in(2x..2x+1, 2y..2y+1))
16:9: h' = w × 9 / 16
```

## 代码走读

文件：[`stages/18_scale_crop/stage.cpp`](stage.cpp)

1. 根据 scale 选 1/2/4 倍。
2. 逐输出像素做 box 平均。
3. 可选中心裁剪，复制到新 Image。

## 跑一跑

```bash
./build/isp_18_scale_crop out/17_hue_saturation.isp out/18_scale_crop.isp --scale 0.5 --crop
```

## 观察与实验

- 0.5/0.25 对比细节。
- `--crop` 与不裁对比构图。
- 先缩放再锐化，对比顺序反过来。

## 常见坑

- 每步都缩放，细节被反复重采样。
- 裁剪不居中，构图偏。
- YUV 的 U/V 单独下采样，颜色错位。

## 为什么放在这个位置

缩放放最后，避免中间阶段反复重采样；裁剪也放最后，先处理完整画面，避免边界效应。

## 自检

- box 平均和双线性缩放的差别？
- 为什么先缩放后锐化会不同？
- 16:9 裁剪会丢多少像素？

---

**上一节** → [Stage 17 · Hue/Saturation](../17_hue_saturation/README.md)  
**下一节** → [Stage 19 · Encoder](../19_encoder/README.md)
