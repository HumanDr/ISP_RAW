# Stage 12 · Color Space：RGB → YUV

> **一句话**：进入 YUV 域，后续只在 Y/U/V 上处理。

## 前后对比

![stage 12](../../docs/images/compare_12.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解 YUV 的用途
- 知道 BT.709 系数
- 会看 U/V 的符号

## 输入 / 输出

| | |
|---|---|
| 输入 | f32 sRGB RGB |
| 输出 | f32 YUV，`space=YUV` |
| 目录 | `stages/12_color_space/` |

## 原理

RGB 三个通道高度相关，直接压缩/降噪效率低。YUV 把亮度 Y 和色度 U/V 分开：人眼对 Y 细节敏感，对 U/V 分辨率不敏感，所以可以分别处理。

本工程用 BT.709 full range，U/V 存 [-0.5,0.5] 的带符号值。

### 公式

```text
Y = 0.2126R + 0.7152G + 0.0722B
U = (B-Y)/1.8556
V = (R-Y)/1.5748
```

## 代码走读

文件：[`stages/12_color_space/stage.cpp`](stage.cpp)

1. 逐像素算 Y/U/V。
2. Y clamp [0,1]，U/V clamp [-0.5,0.5]。
3. 设置 `img.space=SPACE_YUV`，后面 stage 会检查。

## 跑一跑

```bash
./build/isp_12_color_space out/11_gamma.isp out/12_color_space.isp
./build/isp_info out/12_color_space.isp
```

## 观察与实验

- 用 `isp_info` 看 `space: YUV`。
- 把 U/V 清零，得到灰度。
- 改系数为 BT.601，看颜色差异。

## 常见坑

- 把 YUV 当 RGB 显示，颜色会错。
- U/V 用 [0,1] 存，后面减 0.5 会出错。
- 在 YUV 里做 CCM，矩阵不再适用。

## 为什么放在这个位置

YUV 是 RGB 域和 YUV 域的分界：之后所有增强都在 Y/U/V 上做，不再反复转 RGB。

## 自检

- 为什么 U/V 可以是负的？
- BT.709 和 BT.601 的差别？
- full range 与 limited range 的差别？

---

**上一节** → [Stage 11 · Gamma](../11_gamma/README.md)  
**下一节** → [Stage 13 · NR Luma](../13_nr_luma/README.md)
