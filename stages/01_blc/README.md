# Stage 01 · BLC：黑电平校正

> **一句话**：传感器“没光”时读出来约 2047，不是 0。

## 前后对比

![stage 01](../../docs/images/compare_01.png)

*左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。*



---

## 本节目标

- 理解黑电平的物理来源
- 知道为什么要按 CFA 位置分别减
- 会看直方图判断下溢

## 输入 / 输出

| | |
|---|---|
| 输入 | u16 Bayer，带 black/white |
| 输出 | f32 Bayer，归一化到 `[0,1]` |
| 目录 | `stages/01_blc/` |

## 原理

CMOS 读出链是“光子 → 电子 → 电压 → 放大器 → ADC”。ADC 的输入不是从 0 开始，而是有一个偏置，保证微弱信号也能被量化。全黑时读出来约 2047 DN，这就是黑电平。

四个 CFA 位置的黑电平可能差 1 个 LSB，但 B 通道白平衡增益是 2.165，乘上去就是 2.165 个 LSB 的固定偏色，所以必须按位置减。

### 公式

```text
v = (raw - black[cfa]) / (white - black[cfa])
然后 clamp 到 [0,1]（可选）
```

## 代码走读

文件：[`stages/01_blc/stage.cpp`](stage.cpp)

1. 先 `require_f32()`，避免 uint16 下溢。
2. `cfa_pos(x,y)` 返回 0..3，对应 R/G/G/B 四个 black。
3. 最后把 black 清零、white 设 1，表示已经归一化。

## 跑一跑

```bash
./build/isp_01_blc out/00_raw_load.isp out/01_blc.isp
./build/isp_dump out/01_blc.isp out/01.png
```

## 观察与实验

- 加 `--noclip`，观察负值（后续乘增益会放大成偏色）。
- 把四个 black 改成同一个值，看暗部是否偏色。
- 用 `isp_dump` 的 `--no-auto` 看绝对亮度。

## 常见坑

- 用 `white` 而不是 `white-black` 做分母，会整体偏暗。
- 先乘白平衡再减黑电平，偏置会被放大。
- 在 u16 上直接减，负值回绕成 65535。

## 为什么放在这个位置

黑电平是加性偏置，必须在任何乘性增益之前处理；否则白平衡会把偏置一起放大，暗部出现固定偏色。

## 自检

- black 写 0 会怎样？
- 为什么四个 CFA 位置要分开减？
- clip 与不 clip 分别适合什么场景？

---

**上一节** → [Stage 00 · RAW 加载](../00_raw_load/README.md)  
**下一节** → [Stage 02 · LSC](../02_lsc/README.md)
