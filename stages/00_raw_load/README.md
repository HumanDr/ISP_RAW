# Stage 00 · RAW 加载

> 把 .raw + .meta 读成单通道 Bayer。

![stage 00](../../docs/images/stage_00.png)

## 这一节在做什么

- 纯 .raw 没有宽高/CFA/黑电平，必须配 .meta。
- 文件大小必须等于 width*height*2（16bit LE）。
- meta 里的 wb / cam_to_xyz 供后面 AWB 和 CCM 使用。

## 跑一跑

```bash
./build/isp_00_raw_load data/sample.raw out/00_raw_load.isp --meta data/sample.meta
```

## 实验

用 xxd 看前两个像素；改 bayer 为 BGGR，看 stage 06 是否错位。

---

**上一节** → 无  
**下一节** → [Stage 01](../01_blc/README.md)
