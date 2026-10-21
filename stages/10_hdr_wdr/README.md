# Stage 10 · HDR/WDR 高光压缩

> 只压 >1 的高光，0..1 不动。

![stage 10](../../docs/images/stage_10.png)

## 这一节在做什么

- v' = 1 + (v-1)/(1+k(v-1))，v>1。
- 避免硬 clip 造成品红高光。
- k 越大压缩越强。

## 跑一跑

```bash
./build/isp_10_hdr_wdr out/09_color_correction.isp out/10_hdr_wdr.isp --strength 0.4
```

## 实验

强度 0/0.5/1 对比金属高光。

---

**上一节** → [Stage 09](../09_color_correction/README.md)  
**下一节** → [Stage 11](../11_gamma/README.md)
