# Stage 11 · Gamma：自动曝光 + sRGB

> **一句话**：线性光不能直接写 8bit。

## 前后对比

![stage 11](../../docs/images/compare_11.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解线性光与显示编码
- 知道 sRGB 不是简单 2.2
- 会看曝光分位数

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 linear sRGB |
| 输出 | f32 sRGB，[0,1] |
| 目录 | `stages/11_gamma/` |

## 原理

人眼对暗部更敏感，显示器/文件格式按 sRGB 编码。线性光直接量化成 8bit，暗部会丢很多层次。

先做自动曝光：取 max(R,G,B) 的 99.5% 分位，缩放到 0.98；再做 sRGB 传输函数。sRGB 在暗部有一段线性（≤0.0031308），不是纯 2.2。

### 公式

```text
v ≤ 0.0031308: 12.92v
否则: 1.055 v^(1/2.4) - 0.055
```

## 代码走读

文件：[`stages/11_gamma/stage.cpp`](stage.cpp)

1. 采样估计 99.5% 分位，避免单个高光影响。
2. `scale = 0.98 / p99.5`，记录到 `img.exposure`。
3. 逐通道 `srgb_encode()`，clamp 到 [0,1]。

## 跑一跑

```bash
./build/isp_11_gamma out/10_hdr_wdr.isp out/11_gamma.isp
./build/isp_11_gamma out/10_hdr_wdr.isp out/11_manual.isp --manual --ev 0.5
```

## 观察与实验

- 手动 EV 扫 -1/0/+1。
- 跳过 Gamma 直接看，解释为什么又暗又脏。
- 用直方图看暗部层次。

## 常见坑

- 用 2.2 代替 sRGB，暗部会偏暗。
- 在 Gamma 后做 CCM/白平衡，线性关系不成立。
- 自动曝光用均值，容易被大面积高光骗。

## 为什么放在这个位置

Gamma 是线性光到显示编码的边界；它必须在 CCM、WDR 之后，Color Space 之前。提前做 Gamma，后面的线性矩阵全部失效。

## 自检

- sRGB 为什么在暗部有一段线性？
- 自动曝光用均值为什么会失败？
- 手动 EV 与曝光时间的关系？

---

**上一节** → [Stage 10 · HDR/WDR](../10_hdr_wdr/README.md)  
**下一节** → [Stage 12 · Color Space](../12_color_space/README.md)
