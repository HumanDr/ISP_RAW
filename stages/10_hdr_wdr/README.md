# Stage 10 · HDR/WDR：高光压缩

> **一句话**：只压缩 >1 的高光，0..1 不动。

## 前后对比

![stage 10](../../docs/images/compare_10.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解硬 clip 的问题
- 会写 soft-knee
- 知道什么时候该用 WDR

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 linear sRGB，可能 >1 |
| 输出 | f32 linear sRGB，高光被压缩 |
| 目录 | `stages/10_hdr_wdr/` |

## 原理

CCM 之后，饱和的高光可能 >1。直接 clamp 会让先饱和的通道停住，后饱和的通道继续，产生品红/偏色高光。

软压缩只处理 >1 的部分：`v' = 1 + (v-1)/(1+k(v-1))`。0..1 完全不变，所以正常颜色不受影响。

### 公式

```text
v' = 1 + (v-1)/(1 + k(v-1)),  v > 1
v' = v,                      v ≤ 1
```

## 代码走读

文件：[`stages/10_hdr_wdr/stage.cpp`](stage.cpp)

1. 逐通道判断 `v>1`。
2. k 是强度，默认 0.4。
3. 压缩后仍然可能 >1，Gamma 前会再 clamp。

## 跑一跑

```bash
./build/isp_10_hdr_wdr out/09_color_correction.isp out/10_hdr_wdr.isp --strength 0.4
```

## 观察与实验

- 强度 0/0.5/1 对比金属高光。
- 找品红高光，看是否恢复。
- 把 k 设 5，画面会整体变灰。

## 常见坑

- 对 0..1 也做压缩，整体变灰。
- 在 Gamma 后做 WDR，高光已经 clip。
- 只压一个通道，颜色会偏。

## 为什么放在这个位置

高光压缩必须在 Gamma 之前：Gamma 会把 >1 的部分压到 1 附近，先做就无法区分“真正的高光”和“已经饱和的通道”。

## 自检

- 硬 clip 为什么会产生品红？
- k 越大画面为什么越灰？
- WDR 和多帧 HDR 的区别？

---

**上一节** → [Stage 09 · Color Correction](../09_color_correction/README.md)  
**下一节** → [Stage 11 · Gamma](../11_gamma/README.md)
