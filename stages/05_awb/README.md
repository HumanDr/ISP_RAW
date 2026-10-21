# Stage 05 · AWB：自动白平衡

> **一句话**：中性物体应该 R=G=B；用灰度世界 + meta 参考增益。

## 前后对比

![stage 05](../../docs/images/compare_05.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解色温与白平衡
- 知道灰度世界的假设和失败场景
- 会读相机 AsShotNeutral

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 Bayer，三通道均值不同 |
| 输出 | f32 Bayer，三通道增益对齐 |
| 目录 | `stages/05_awb/` |

## 原理

白平衡要解决的是“光源颜色”而不是“物体颜色”。如果一张白纸在暖光下拍出来偏黄，我们需要乘一个蓝色增益，把白纸拉回中性。

灰度世界假设整幅图平均是灰色：`gain_c = mean_G / mean_c`。单色场景（草地、蓝天）会失败。所以本工程把灰度世界和 meta 里的相机参考增益按 `--strength` 混合。

### 公式

```text
gain_c = mean_G / mean_c
out_c = in_c × gain_c
```

## 代码走读

文件：[`stages/05_awb/stage.cpp`](stage.cpp)

1. 统计 CFA 三通道均值，排除 >0.95 的高光。
2. `strength` 控制灰度世界与 meta 增益的混合。
3. G 增益强制为 1，避免整体变亮/变暗。

## 跑一跑

```bash
./build/isp_05_awb out/04_nr_raw.isp out/05_awb.isp --strength 0.5
./build/isp_05_awb out/04_nr_raw.isp out/05_meta.isp --no-gray-world
```

## 观察与实验

- 对比灰度世界与相机参考。
- 用大面积单色图解释灰度世界为什么失败。
- 把 strength 调到 1，看暖光场景是否被拉得过冷。

## 常见坑

- 在去马赛克后做 AWB，插值会改变通道统计。
- 统计包含高光，饱和像素把均值拉偏。
- 把 G 也乘增益，整体曝光变了。

## 为什么放在这个位置

白平衡是乘性增益，必须放在去马赛克之前：Bayer 上每个像素只有一种颜色，乘增益不会引入插值误差；放到后面反而会把插值误差一起放大。

## 自检

- 灰度世界在什么场景会失败？
- 为什么 G 增益固定为 1？
- AsShotNeutral 与 RGB 增益如何互换？

---

**上一节** → [Stage 04 · NR RAW](../04_nr_raw/README.md)  
**下一节** → [Stage 06 · Demosaic](../06_demosaic/README.md)
