from pathlib import Path

DATA = [
("00","raw_load","RAW 加载","把 .raw + .meta 读成单通道 Bayer。",[
"纯 .raw 没有宽高/CFA/黑电平，必须配 .meta。",
"文件大小必须等于 width*height*2（16bit LE）。",
"meta 里的 wb / cam_to_xyz 供后面 AWB 和 CCM 使用。"],
"./build/isp_00_raw_load data/sample.raw out/00_raw_load.isp --meta data/sample.meta",
"用 xxd 看前两个像素；改 bayer 为 BGGR，看 stage 06 是否错位。"),

("01","blc","BLC 黑电平校正","传感器没光时读出来约 2047，不是 0。",[
"公式：v = (raw - black[cfa]) / (white - black[cfa])。",
"四个 CFA 位置分别减，避免 B 增益放大成偏色。",
"先转 f32 再减，防止 uint16 下溢。"],
"./build/isp_01_blc out/00_raw_load.isp out/01_blc.isp",
"加 --noclip 看负值；把四个 black 改成同一个值看暗部偏色。"),

("02","lsc","LSC 镜头阴影校正","cos⁴ 暗角，用径向增益把四角提亮。",[
"按半径分桶，每个 CFA 通道取亮度中位数。",
"gain(r) = profile(0) / profile(r)，再平滑、限幅。",
"真实产品用 flat-field；本工程是场景统计近似。"],
"./build/isp_02_lsc out/01_blc.isp out/02_lsc.isp --strength 0.7",
"强度 0/0.5/1 对比四角；换平坦场景看估计是否更准。"),

("03","dpc","BPC/DPC 坏点校正","hot/dead pixel 是孤立极值，用同色 4 邻域中值替换。",[
"同色邻居在上下左右各隔 2 像素。",
"判据：中心是 5 个数的极值，且 |v-med| > threshold。",
"不能修大片 cluster 缺陷。"],
"./build/isp_03_dpc out/02_lsc.isp out/03_dpc.isp --threshold 0.05",
"阈值 0.01/0.05/0.2 对比；自己注入 0/65535 看修复。"),

("04","nr_raw","NR RAW 降噪","在 Bayer 上做双边，只采样同色邻居。",[
"w = exp(-dxy²/2σs²)·exp(-(I(p)-I(q))²/2σr²)。",
"同色条件：dx+dy 为偶数。",
"RAW 域先降噪，避免去马赛克把噪声变成彩色斑块。"],
"./build/isp_04_nr_raw out/03_dpc.isp out/04_nr_raw.isp",
"--sigma 0 自动；手动 0.02 对比噪声/细节。"),

("05","awb","AWB 自动白平衡","中性物体应该 R=G=B。",[
"灰度世界：gain_c = mean_G / mean_c。",
"单色场景会失败，所以和 meta 参考增益按 strength 混合。",
"统计时排除 >0.95 的高光。"],
"./build/isp_05_awb out/04_nr_raw.isp out/05_awb.isp --strength 0.5",
"对比 --no-gray-world；用大面积单色图解释灰度世界为什么失败。"),

("06","demosaic","Demosaic 去马赛克","每个像素只有一个颜色，另外两个靠邻居插值。",[
"双线性：G 取上下左右平均，R/B 取对角平均。",
"MHC：5×5 卷积 + 已知通道梯度修正，伪彩更少。",
"输出变成 3 通道 RGB。"],
"./build/isp_06_demosaic out/05_awb.isp out/06_demosaic.isp",
"对比 --method bilinear；100% 裁切看拉链纹/伪彩。"),

("07","nr_color","NR Color 色度降噪","转 YUV，只对 U/V 做中值，Y 保持。",[
"Y=0.2126R+0.7152G+0.0722B。",
"U=(B-Y)/1.8556，V=(R-Y)/1.5748。",
"人眼对色度分辨率低，所以可以只降色度。"],
"./build/isp_07_nr_color out/06_demosaic.isp out/07_nr_color.isp --strength 0.4",
"强度 0/0.5/1 对比彩色噪点；观察颜色边缘是否渗色。"),

("08","xtalk","X-talking 串扰校正","滤光片不是理想窄带，R/G/B 会互相漏。",[
"R'=R-kG-kB，G'=-kR+G-kB，B'=-kR-kG+B。",
"按行归一化，保证白点不变。",
"k 越大颜色越分离，也越容易过饱和。"],
"./build/isp_08_xtalk out/07_nr_color.isp out/08_xtalk.isp --strength 0.04",
"强度 0/0.05/0.1 对比肤色和金属高光。"),

("09","color_correction","Color Correction 颜色校正","相机 RGB → XYZ → linear sRGB。",[
"M = XYZ_to_sRGB · cam_to_xyz。",
"每行归一化，保证 (1,1,1) 仍是 (1,1,1)。",
"负系数会放大噪声和伪彩。"],
"./build/isp_09_color_correction out/08_xtalk.isp out/09_color_correction.isp",
"把 cam_to_xyz 改成单位矩阵看颜色崩坏；去掉行归一化看偏色。"),

("10","hdr_wdr","HDR/WDR 高光压缩","只压 >1 的高光，0..1 不动。",[
"v' = 1 + (v-1)/(1+k(v-1))，v>1。",
"避免硬 clip 造成品红高光。",
"k 越大压缩越强。"],
"./build/isp_10_hdr_wdr out/09_color_correction.isp out/10_hdr_wdr.isp --strength 0.4",
"强度 0/0.5/1 对比金属高光。"),

("11","gamma","Gamma 自动曝光 + sRGB","线性光不能直接写 8bit。",[
"用 99.5% 分位数自动曝光。",
"sRGB：v<=0.0031308 时 12.92v，否则 1.055v^(1/2.4)-0.055。",
"Gamma 必须在 CCM 之后。"],
"./build/isp_11_gamma out/10_hdr_wdr.isp out/11_gamma.isp",
"--manual --ev 0.5 对比；跳过 Gamma 直接看为什么又暗又脏。"),

("12","color_space","Color Space RGB→YUV","进入 YUV 域。",[
"Y=0.2126R+0.7152G+0.0722B。",
"U=(B-Y)/1.8556，V=(R-Y)/1.5748。",
"输出 .isp 的 space 标记为 YUV。"],
"./build/isp_12_color_space out/11_gamma.isp out/12_color_space.isp",
"用 isp_info 看 space: YUV；把 U/V 清零得到灰度。"),

("13","nr_luma","NR Luma 亮度降噪","只对 Y 做小半径双边。",[
"Y 同时承载亮度和细节，σ 要小。",
"默认 σ=0.012；太大画面会变塑料。",
"U/V 完全不动。"],
"./build/isp_13_nr_luma out/12_color_space.isp out/13_nr_luma.isp --sigma 0.012",
"σ 0/0.02/0.05 对比暗部噪声和细节。"),

("14","edge_enhance","Edge Enhance 边缘增强","只增强 Y，避免彩色描边。",[
"Y' = Y + amount·(Y - blur(Y))。",
"|detail| < 0.004 时不处理，避免放大噪声。",
"3×3 可分离高斯。"],
"./build/isp_14_edge_enhance out/13_nr_luma.isp out/14_edge_enhance.isp --amount 0.4",
"amount 0/0.5/1.5 对比白边和噪点。"),

("15","contrast_brightness","Contrast/Brightness 对比度","只改 Y。",[
"Y' = (Y-0.5)·contrast + 0.5 + brightness。",
"对比度太大暗部死黑、亮部死白。",
"U/V 不动，色相不变。"],
"./build/isp_15_contrast_brightness out/14_edge_enhance.isp out/15_contrast_brightness.isp --contrast 1.05",
"对比度 0.8/1.0/1.3；亮度 ±0.05 看直方图。"),

("16","nr_chroma","NR Chroma 色度降噪","U/V 的 3×3 中值。",[
"人眼对色度分辨率低，可以比亮度更激进。",
"中值去孤立彩色噪点。",
"太强会让颜色边界渗色。"],
"./build/isp_16_nr_chroma out/15_contrast_brightness.isp out/16_nr_chroma.isp --strength 0.4",
"强度 0/0.5/1 对比彩色噪点。"),

("17","hue_saturation","Hue/Saturation 色调饱和","旋转 (U,V) 并缩放饱和度。",[
"u'=(u cosθ - v sinθ)·sat。",
"v'=(u sinθ + v cosθ)·sat。",
"Y 不变，只改色度。"],
"./build/isp_17_hue_saturation out/16_nr_chroma.isp out/17_hue_saturation.isp --sat 1.08",
"sat 0.5/1/1.5；hue ±30° 看肤色。"),

("18","scale_crop","Scale & Crop 缩放裁剪","最后再缩放，避免中间反复重采样。",[
"支持 1/2、1/4 box 平均。",
"--crop 中心裁成 16:9。",
"缩放放在 YUV 域。"],
"./build/isp_18_scale_crop out/17_hue_saturation.isp out/18_scale_crop.isp --scale 0.5 --crop",
"0.5/0.25 对比细节；--crop 与不裁对比构图。"),

("19","encoder","Encoder 输出 PNG/YUV","YUV→RGB 写 PNG；可选 YUV420。",[
"R=Y+1.5748V。",
"G=Y-0.1873U-0.4681V。",
"B=Y+1.8556U。",
"--yuv 写 YUV420 planar。"],
"./build/isp_19_encoder out/18_scale_crop.isp out/final.png --yuv",
"看 PNG/YUV 文件大小；用 ffmpeg 读 YUV420 确认格式。"),
]

def write():
    for i, (num, d, title, short, pts, cmd, exp) in enumerate(DATA):
        prev = f"[Stage {i-1:02d}](../{DATA[i-1][0]}_{DATA[i-1][1]}/README.md)" if i else "无"
        nxt = f"[Stage {i+1:02d}](../{DATA[i+1][0]}_{DATA[i+1][1]}/README.md)" if i < 19 else "[课程首页](../../README.md)"
        body = "\n".join(f"- {p}" for p in pts)
        text = f"""# Stage {num} · {title}

> {short}

![stage {num}](../../docs/images/stage_{num}.png)

## 这一节在做什么

{body}

## 跑一跑

```bash
{cmd}
```

## 实验

{exp}

---

**上一节** → {prev}  
**下一节** → {nxt}
"""
        Path(f"stages/{num}_{d}/README.md").write_text(text, encoding="utf-8")
    print("wrote", len(DATA))

if __name__ == "__main__":
    write()
