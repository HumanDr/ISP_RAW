from pathlib import Path

D = []
def add(num, d, title, short, inp, outp, goals, principle, formula, code, cmd, exp, pitfall):
    D.append(dict(num=num, d=d, title=title, short=short, inp=inp, outp=outp,
                  goals=goals, principle=principle, formula=formula, code=code,
                  cmd=cmd, exp=exp, pitfall=pitfall))

add("00","raw_load","RAW 加载：.raw + .meta → Bayer",
    "把无文件头的 16bit RAW 和一份 meta 读成单通道 Bayer。",
    "`data/sample.raw` + `data/sample.meta`", "单通道 `Image`，`dtype=U16`，`cfa=RGGB`",
    ["理解纯 .raw 为什么必须配 meta", "知道 Bayer 2×2 的四个位置", "会检查文件大小和字节序"],
    "纯 `.raw` 只有像素，没有宽高、CFA、黑电平。ISP 必须先从 `.meta` 知道“这张图多大、什么 Bayer 排列、黑白电平是多少、白平衡和颜色矩阵是什么”。\n\n本工程把 meta 做成一行的文本，而不是二进制头。这样你可以用记事本改一个 black 值，重新跑 stage 01，立刻看到直方图变化，不需要重新编译。",
    "文件大小 = width × height × 2（16bit little-endian）\nBayer 2×2：\nR G\nG B   （RGGB）",
    ["`load_raw_meta()` 逐行解析 key/value；`#` 开头是注释。",
     "`load_raw()` 检查文件大小必须正好等于 `w*h*2`，否则直接报错。",
     "CFA 字符串映射到 `CFA_RGGB/BGGR/GRBG/GBRG`，后面所有 `cfa_color()` 都依赖它。"],
    "./build/isp_00_raw_load data/sample.raw out/00_raw_load.isp --meta data/sample.meta\n./build/isp_info out/00_raw_load.isp",
    ["`xxd -l 32 data/sample.raw`：前两个 16bit 就是左上角 R/G。",
     "把 meta 的 `bayer` 改成 `BGGR`，跑 stage 06，看颜色是否错位。",
     "把 `width` 改错 1，确认程序会报“文件大小不对”。"],
    ["把 `.raw` 当成有文件头的格式，直接读像素会整体偏移。",
     "忽略字节序：大端机器读小端数据会得到荒谬的数值。",
     "meta 的 black/white 写错，后面所有阶段都会跟着错。"])

add("01","blc","BLC：黑电平校正",
    "传感器“没光”时读出来约 2047，不是 0。",
    "u16 Bayer，带 black/white", "f32 Bayer，归一化到 `[0,1]`",
    ["理解黑电平的物理来源", "知道为什么要按 CFA 位置分别减", "会看直方图判断下溢"],
    "CMOS 读出链是“光子 → 电子 → 电压 → 放大器 → ADC”。ADC 的输入不是从 0 开始，而是有一个偏置，保证微弱信号也能被量化。全黑时读出来约 2047 DN，这就是黑电平。\n\n四个 CFA 位置的黑电平可能差 1 个 LSB，但 B 通道白平衡增益是 2.165，乘上去就是 2.165 个 LSB 的固定偏色，所以必须按位置减。",
    "v = (raw - black[cfa]) / (white - black[cfa])\n然后 clamp 到 [0,1]（可选）",
    ["先 `require_f32()`，避免 uint16 下溢。",
     "`cfa_pos(x,y)` 返回 0..3，对应 R/G/G/B 四个 black。",
     "最后把 black 清零、white 设 1，表示已经归一化。"],
    "./build/isp_01_blc out/00_raw_load.isp out/01_blc.isp\n./build/isp_dump out/01_blc.isp out/01.png",
    ["加 `--noclip`，观察负值（后续乘增益会放大成偏色）。",
     "把四个 black 改成同一个值，看暗部是否偏色。",
     "用 `isp_dump` 的 `--no-auto` 看绝对亮度。"],
    ["用 `white` 而不是 `white-black` 做分母，会整体偏暗。",
     "先乘白平衡再减黑电平，偏置会被放大。",
     "在 u16 上直接减，负值回绕成 65535。"])

add("02","lsc","LSC：镜头阴影校正",
    "cos⁴ 暗角，用径向增益把四角提亮。",
    "f32 Bayer，已减黑电平", "f32 Bayer，四角提亮",
    ["理解暗角的来源", "会从图像统计估计径向增益", "知道 flat-field 标定与统计近似的差别"],
    "镜头是有限口径的光学系统，边缘光线入射角大，照度按 cos⁴ 衰减；再加上微透镜和 CFA 的串扰，四角会明显变暗。\n\n工业做法是用均匀白板拍 flat-field，直接得到每个像素的增益。本工程没有标定数据，只能按半径分桶，取每个 CFA 通道的亮度中位数，得到 `profile(r)`，再算 `gain(r)=profile(0)/profile(r)`。场景内容会污染估计，所以默认强度只给 0.7。",
    "gain(r) = profile(0) / profile(r)\nprofile(r) = median(luma at radius r)",
    ["按 64 个半径桶累积直方图，求中位数。",
     "对 profile 做 5 点平滑，避免桶边界跳变。",
     "增益限幅到 [1, 2.5]，再做双线性插值。"],
    "./build/isp_02_lsc out/01_blc.isp out/02_lsc.isp --strength 0.7\n./build/isp_dump out/02_lsc.isp out/02.png",
    ["`--strength 0/0.5/1` 对比四角。",
     "换一张四角有内容的图，估计会变差——解释“为什么需要 flat-field”。",
     "把强度设 1，观察四角噪声是否被放大。"],
    ["用整幅图的全局均值做参考，会把场景亮度当成暗角。",
     "增益不限幅，四角噪声会被过度放大。",
     "在每个 CFA 通道分别估计后忘记平滑，会出现色块。"])

add("03","dpc","BPC/DPC：坏点校正",
    "hot/dead pixel 是孤立极值，用同色 4 邻域中值替换。",
    "f32 Bayer", "f32 Bayer，坏点被替换",
    ["理解 hot/dead pixel", "知道同色邻居在 Bayer 上的位置", "会调阈值避免误伤细节"],
    "坏点是制造缺陷：某个像素对光不敏感（dead）或暗电流特别大（hot）。它在图像上是一个孤立亮点/暗点。\n\nBayer 上同色邻居在上下左右各隔 2 像素。取 4 个同色邻居的中值 `med`；如果中心是这 5 个数里的极值，且 `|v-med| > threshold`，就用 `med` 替换。这个方法不能修大片 cluster 缺陷。",
    "if (v <= min(n) or v >= max(n)) and |v - med| > T:\nv = med",
    ["跳过最外 2 像素，避免越界。",
     "排序 4 个同色邻居，取中间两个的平均。",
     "阈值是归一化后的值，默认 0.05（约 750 DN）。"],
    "./build/isp_03_dpc out/02_lsc.isp out/03_dpc.isp --threshold 0.05",
    ["阈值 0.01/0.05/0.2，看修复像素数。",
     "往 raw 里注入几个 0/65535，确认能修。",
     "把阈值设成 0，观察正常细节被误伤。"],
    ["把非同色邻居拿来取中值，会引入彩色伪影。",
     "阈值太小，把高频细节当坏点。",
     "修完不检查边界，最外圈会出现黑边。"])

add("04","nr_raw","NR RAW：RAW 域降噪",
    "在 Bayer 上做双边，只采样同色邻居。",
    "f32 Bayer", "f32 Bayer，噪声降低",
    ["理解光子噪声/读出噪声", "知道双边滤波的空间项和值域项", "会权衡降噪与细节"],
    "RAW 噪声由光子噪声（与信号平方根相关）和读出噪声（与信号无关）组成，越暗越脏。\n\n双边滤波同时看空间距离和像素值差：空间近、值也近的邻居权重大。只取 `dx+dy` 为偶数的同色邻居，避免把 R/G/B 混在一起。σ_range 可以用相邻同色像素差的中位数自动估计。",
    "w = exp(-(dx²+dy²)/2σs²) · exp(-(I(p)-I(q))²/2σr²)",
    ["`estimate_noise()` 用相邻同色像素差的中位数估计噪声。",
     "12 个同色邻居，空间权重预计算。",
     "值域权重用 1024 项 LUT，避免 exp 太慢。"],
    "./build/isp_04_nr_raw out/03_dpc.isp out/04_nr_raw.isp\n./build/isp_dump out/04_nr_raw.isp out/04.png",
    ["`--sigma 0` 自动估计；手动 0.02 对比。",
     "看暗部噪声和边缘细节的取舍。",
     "σ 太大，去马赛克后会出现“蜡像”皮肤。"],
    ["对全部邻居采样，把不同颜色混在一起。",
     "σ_range 设得比噪声大很多，边缘被糊掉。",
     "先做 Gamma 再降噪，噪声模型不再线性。"])

add("05","awb","AWB：自动白平衡",
    "中性物体应该 R=G=B；用灰度世界 + meta 参考增益。",
    "f32 Bayer，三通道均值不同", "f32 Bayer，三通道增益对齐",
    ["理解色温与白平衡", "知道灰度世界的假设和失败场景", "会读相机 AsShotNeutral"],
    "白平衡要解决的是“光源颜色”而不是“物体颜色”。如果一张白纸在暖光下拍出来偏黄，我们需要乘一个蓝色增益，把白纸拉回中性。\n\n灰度世界假设整幅图平均是灰色：`gain_c = mean_G / mean_c`。单色场景（草地、蓝天）会失败。所以本工程把灰度世界和 meta 里的相机参考增益按 `--strength` 混合。",
    "gain_c = mean_G / mean_c\nout_c = in_c × gain_c",
    ["统计 CFA 三通道均值，排除 >0.95 的高光。",
     "`strength` 控制灰度世界与 meta 增益的混合。",
     "G 增益强制为 1，避免整体变亮/变暗。"],
    "./build/isp_05_awb out/04_nr_raw.isp out/05_awb.isp --strength 0.5\n./build/isp_05_awb out/04_nr_raw.isp out/05_meta.isp --no-gray-world",
    ["对比灰度世界与相机参考。",
     "用大面积单色图解释灰度世界为什么失败。",
     "把 strength 调到 1，看暖光场景是否被拉得过冷。"],
    ["在去马赛克后做 AWB，插值会改变通道统计。",
     "统计包含高光，饱和像素把均值拉偏。",
     "把 G 也乘增益，整体曝光变了。"])

add("06","demosaic","Demosaic：去马赛克",
    "每个像素只有一个颜色，另外两个靠邻居插值。",
    "f32 Bayer", "f32 RGB，三通道",
    ["理解 Bayer 的采样率", "知道双线性和 MHC 的差别", "会看伪彩和拉链纹"],
    "Bayer 上 R/B 各占 25%，G 占 50%。每个像素缺少两个颜色，必须插值。双线性是邻居平均，快，但在黑白边缘会产生拉链纹和伪彩。\n\nMalvar-He-Cutler 用 5×5 卷积，同时利用已知通道的梯度修正未知通道，边缘更干净。代价是计算量更大。",
    "G = (G左+G右+G上+G下)/4\nMHC：5×5 卷积 + 已知通道梯度修正",
    ["`bilinear()` 处理边界和 G 像素的两种方向。",
     "MHC 用 4 个卷积核：kG、kRgH、kRgV、kRb。",
     "输出分配新 3 通道 `Image`，`space=RGB`。"],
    "./build/isp_06_demosaic out/05_awb.isp out/06_demosaic.isp\n./build/isp_06_demosaic out/05_awb.isp out/06_bilinear.isp --method bilinear",
    ["100% 裁切对比 bilinear/MHC。",
     "找黑白边界，观察伪彩。",
     "把 CFA 改错，看颜色错位。"],
    ["在 Gamma 后去马赛克，插值不再是线性的。",
     "只对 R/B 插值，G 不插，边缘会偏绿。",
     "边界不 clamp，5×5 卷积会越界。"])

add("07","nr_color","NR Color：RGB 域色度降噪",
    "转 YUV，只对 U/V 做 3×3 中值，Y 保持。",
    "f32 RGB", "f32 RGB，色度噪声降低",
    ["理解亮度/色度分离", "知道为什么只降色度", "会看彩色斑块"],
    "去马赛克会把 RAW 噪声变成彩色斑块。人眼对色度空间分辨率低，所以可以只降色度，保留亮度细节。\n\n先把 RGB 转 YUV，对 U/V 做 3×3 中值，再按 `strength` 和原值混合，最后转回 RGB。中值能去掉孤立彩色噪点，但太强会让颜色边界渗色。",
    "Y=0.2126R+0.7152G+0.0722B\nU=(B-Y)/1.8556, V=(R-Y)/1.5748",
    ["转 YUV 后分别存 Y/U/V。",
     "对 U/V 做 3×3 中值（排序 9 个数取中间）。",
     "按 strength 混合，再 YUV→RGB。"],
    "./build/isp_07_nr_color out/06_demosaic.isp out/07_nr_color.isp --strength 0.4",
    ["强度 0/0.5/1 对比彩色噪点。",
     "看颜色边缘是否渗色。",
     "对比只降 Y 的效果：细节会变糊。"],
    ["在 RGB 三通道各自中值，会把颜色边界弄脏。",
     "强度 1，肤色会变成色块。",
     "YUV 转换公式和后面的 BT.709 不一致，颜色会偏。"])

add("08","xtalk","X-talking：颜色串扰校正",
    "滤光片不是理想窄带，R/G/B 会互相漏。",
    "f32 RGB", "f32 RGB，通道串扰降低",
    ["理解 CFA 光谱串扰", "会构造 3×3 校正矩阵", "知道过校正的后果"],
    "CFA 的 R/G/B 滤光片不是理想窄带，红光会漏进 G/B，蓝光会漏进 G。结果就是颜色“发灰”、饱和度下降。\n\n用 3×3 矩阵去掉非对角项：对角 1，非对角 `-k`，再按行归一化，保证白点不变。`k` 越大颜色越分离，也越容易过饱和。",
    "R' = R - kG - kB\nG' = -kR + G - kB\nB' = -kR - kG + B\n（每行除以行和）",
    ["构造 `I - k(ones-I)`。",
     "每行除以行和，保证 (1,1,1)→(1,1,1)。",
     "逐像素矩阵乘，负值 clamp 到 0。"],
    "./build/isp_08_xtalk out/07_nr_color.isp out/08_xtalk.isp --strength 0.04",
    ["强度 0/0.05/0.1 对比肤色。",
     "看金属高光是否过饱和。",
     "把 k 设 0.3，观察颜色崩坏。"],
    ["不做行归一化，整体亮度会变。",
     "在 Gamma 后做串扰校正，线性关系不成立。",
     "k 太大，暗部负值被 clamp，颜色出现死区。"])

add("09","color_correction","Color Correction：颜色校正矩阵",
    "相机 RGB → XYZ → linear sRGB。",
    "f32 RGB，相机色彩空间", "f32 RGB，linear sRGB",
    ["理解 CCM 的作用", "知道 cam_to_xyz 的方向", "会看行归一化和负系数"],
    "相机 RGB 不是 sRGB。不同 CFA 的光谱响应不同，同一块中性灰在相机里可能是 (0.4, 0.5, 0.3)。CCM 把这个“相机色彩空间”映射到 CIE XYZ，再映射到 sRGB。\n\nmeta 里的 `cam_to_xyz` 已经包含白平衡后的相机 RGB → XYZ(D65)。本工程再乘 XYZ→sRGB，得到最终矩阵。每行归一化，保证白点不变。",
    "M = XYZ_to_sRGB · cam_to_xyz\nout = M · rgb",
    ["`mat3_mul` 做 3×3 乘法。",
     "每行除以行和，保证 (1,1,1) 仍是白。",
     "逐像素矩阵乘，负值 clamp。"],
    "./build/isp_09_color_correction out/08_xtalk.isp out/09_color_correction.isp",
    ["把 `cam_to_xyz` 改成单位矩阵，看颜色如何变化。",
     "去掉行归一化，观察整体偏色。",
     "看矩阵的负系数，解释为什么暗部噪声会被放大。"],
    ["把矩阵方向弄反（XYZ→相机 vs 相机→XYZ）。",
     "在 Gamma 后做 CCM，线性关系不成立。",
     "不 clamp 负值，后续 Gamma 会出现 NaN。"])

add("10","hdr_wdr","HDR/WDR：高光压缩",
    "只压缩 >1 的高光，0..1 不动。",
    "f32 linear sRGB，可能 >1", "f32 linear sRGB，高光被压缩",
    ["理解硬 clip 的问题", "会写 soft-knee", "知道什么时候该用 WDR"],
    "CCM 之后，饱和的高光可能 >1。直接 clamp 会让先饱和的通道停住，后饱和的通道继续，产生品红/偏色高光。\n\n软压缩只处理 >1 的部分：`v' = 1 + (v-1)/(1+k(v-1))`。0..1 完全不变，所以正常颜色不受影响。",
    "v' = 1 + (v-1)/(1 + k(v-1)),  v > 1\nv' = v,                      v ≤ 1",
    ["逐通道判断 `v>1`。",
     "k 是强度，默认 0.4。",
     "压缩后仍然可能 >1，Gamma 前会再 clamp。"],
    "./build/isp_10_hdr_wdr out/09_color_correction.isp out/10_hdr_wdr.isp --strength 0.4",
    ["强度 0/0.5/1 对比金属高光。",
     "找品红高光，看是否恢复。",
     "把 k 设 5，画面会整体变灰。"],
    ["对 0..1 也做压缩，整体变灰。",
     "在 Gamma 后做 WDR，高光已经 clip。",
     "只压一个通道，颜色会偏。"])

add("11","gamma","Gamma：自动曝光 + sRGB",
    "线性光不能直接写 8bit。",
    "f32 linear sRGB", "f32 sRGB，[0,1]",
    ["理解线性光与显示编码", "知道 sRGB 不是简单 2.2", "会看曝光分位数"],
    "人眼对暗部更敏感，显示器/文件格式按 sRGB 编码。线性光直接量化成 8bit，暗部会丢很多层次。\n\n先做自动曝光：取 max(R,G,B) 的 99.5% 分位，缩放到 0.98；再做 sRGB 传输函数。sRGB 在暗部有一段线性（≤0.0031308），不是纯 2.2。",
    "v ≤ 0.0031308: 12.92v\n否则: 1.055 v^(1/2.4) - 0.055",
    ["采样估计 99.5% 分位，避免单个高光影响。",
     "`scale = 0.98 / p99.5`，记录到 `img.exposure`。",
     "逐通道 `srgb_encode()`，clamp 到 [0,1]。"],
    "./build/isp_11_gamma out/10_hdr_wdr.isp out/11_gamma.isp\n./build/isp_11_gamma out/10_hdr_wdr.isp out/11_manual.isp --manual --ev 0.5",
    ["手动 EV 扫 -1/0/+1。",
     "跳过 Gamma 直接看，解释为什么又暗又脏。",
     "用直方图看暗部层次。"],
    ["用 2.2 代替 sRGB，暗部会偏暗。",
     "在 Gamma 后做 CCM/白平衡，线性关系不成立。",
     "自动曝光用均值，容易被大面积高光骗。"])

add("12","color_space","Color Space：RGB → YUV",
    "进入 YUV 域，后续只在 Y/U/V 上处理。",
    "f32 sRGB RGB", "f32 YUV，`space=YUV`",
    ["理解 YUV 的用途", "知道 BT.709 系数", "会看 U/V 的符号"],
    "RGB 三个通道高度相关，直接压缩/降噪效率低。YUV 把亮度 Y 和色度 U/V 分开：人眼对 Y 细节敏感，对 U/V 分辨率不敏感，所以可以分别处理。\n\n本工程用 BT.709 full range，U/V 存 [-0.5,0.5] 的带符号值。",
    "Y = 0.2126R + 0.7152G + 0.0722B\nU = (B-Y)/1.8556\nV = (R-Y)/1.5748",
    ["逐像素算 Y/U/V。",
     "Y clamp [0,1]，U/V clamp [-0.5,0.5]。",
     "设置 `img.space=SPACE_YUV`，后面 stage 会检查。"],
    "./build/isp_12_color_space out/11_gamma.isp out/12_color_space.isp\n./build/isp_info out/12_color_space.isp",
    ["用 `isp_info` 看 `space: YUV`。",
     "把 U/V 清零，得到灰度。",
     "改系数为 BT.601，看颜色差异。"],
    ["把 YUV 当 RGB 显示，颜色会错。",
     "U/V 用 [0,1] 存，后面减 0.5 会出错。",
     "在 YUV 里做 CCM，矩阵不再适用。"])

add("13","nr_luma","NR Luma：亮度降噪",
    "只对 Y 做小半径双边，U/V 不动。",
    "f32 YUV", "f32 YUV，Y 噪声降低",
    ["理解亮度噪声", "知道 σ 的取舍", "会看细节损失"],
    "Y 同时承载亮度和细节。σ 太大画面会“塑料”，太小噪声还在。\n\n3×3 双边，空间权重中心 1.6、十字 1.0、对角 0.7；值域权重用 LUT。只改 channel 0。",
    "w = spatial · exp(-(Y(p)-Y(q))²/2σ²)",
    ["复制 Y 到临时数组。",
     "3×3 双边，只写回 `p[i*3]`。",
     "σ 默认 0.012。"],
    "./build/isp_13_nr_luma out/12_color_space.isp out/13_nr_luma.isp --sigma 0.012",
    ["σ 0/0.02/0.05 对比。",
     "看暗部噪声和细节。",
     "对比只降 Y 和只降 U/V 的差别。"],
    ["对 YUV 三个通道一起双边，色度会串。",
     "σ 太大，边缘变糊。",
     "在 Gamma 前做，噪声模型不同。"])

add("14","edge_enhance","Edge Enhance：边缘增强",
    "只增强 Y，避免彩色描边。",
    "f32 YUV", "f32 YUV，Y 边缘增强",
    ["理解 unsharp mask", "知道为什么要阈值", "会看白边/光晕"],
    "对 Y 做 3×3 高斯模糊，取 `detail = Y - blur(Y)`，再 `Y' = Y + amount·detail`。\n\n`|detail| < 0.004` 时不处理，避免放大噪声。只改 Y，所以不会出现彩色描边。",
    "Y' = Y + amount · (Y - blur(Y))",
    ["可分离 3×3 高斯：先横后纵。",
     "细节小于阈值跳过。",
     "结果 clamp [0,1]。"],
    "./build/isp_14_edge_enhance out/13_nr_luma.isp out/14_edge_enhance.isp --amount 0.4",
    ["amount 0/0.5/1.5 对比白边。",
     "看彩色边缘是否出现描边。",
     "先降噪再锐化，对比顺序反过来。"],
    ["对 RGB 三通道分别锐化，彩色边缘会描边。",
     "amount 太大，白边/光晕明显。",
     "不设阈值，噪声被放大。"])

add("15","contrast_brightness","Contrast/Brightness：对比度/亮度",
    "只改 Y：Y' = (Y-0.5)·contrast + 0.5 + brightness。",
    "f32 YUV", "f32 YUV，Y 对比度/亮度改变",
    ["理解线性对比度", "知道死黑/死白", "会看直方图"],
    "这是显示端的线性对比度/亮度，不改变色度。对比度太大暗部会死黑、亮部会死白；亮度偏移会让整体变亮/变暗。\n\n只改 Y，U/V 不变，所以色相不变。",
    "Y' = (Y - 0.5) × contrast + 0.5 + brightness",
    ["逐像素只改 channel 0。",
     "clamp 到 [0,1]。",
     "默认 contrast 1.05，brightness 0.005。"],
    "./build/isp_15_contrast_brightness out/14_edge_enhance.isp out/15_contrast_brightness.isp --contrast 1.05 --brightness 0.005",
    ["对比度 0.8/1.0/1.3。",
     "亮度 ±0.05，看直方图。",
     "把 contrast 设 2，观察死黑。"],
    ["对 RGB 三通道做对比度，饱和度会变。",
     "在 Gamma 前做，线性关系不同。",
     "不 clamp，后面量化会回绕。"])

add("16","nr_chroma","NR Chroma：色度降噪",
    "U/V 的 3×3 中值，比亮度更激进。",
    "f32 YUV", "f32 YUV，U/V 噪声降低",
    ["理解色度噪声", "知道中值的优缺点", "会看颜色渗色"],
    "人眼对色度空间分辨率低，所以 U/V 可以做强降噪。中值能去掉孤立彩色噪点，但会让颜色边界轻微渗色。\n\n对 U/V 各做 3×3 中值，按 `strength` 混合。Y 不动。",
    "U' = median(U 3×3), V' = median(V 3×3)\nU = (1-s)U + sU'",
    ["分别复制 U/V。",
     "对每个像素排序 9 个数取中间。",
     "按 strength 混合，写回 channel 1/2。"],
    "./build/isp_16_nr_chroma out/15_contrast_brightness.isp out/16_nr_chroma.isp --strength 0.4",
    ["强度 0/0.5/1。",
     "看彩色噪点和颜色边缘。",
     "和 stage 07 对比：一个在 RGB 域，一个在 YUV 域。"],
    ["中值窗口太大，颜色边界渗色。",
     "对 Y 也做中值，细节丢失。",
     "强度 1，肤色变成色块。"])

add("17","hue_saturation","Hue/Saturation：色相与饱和度",
    "在 YUV 里旋转 (U,V)，再缩放饱和度。",
    "f32 YUV", "f32 YUV，色相/饱和度改变",
    ["理解色相旋转", "知道饱和度的含义", "会看肤色"],
    "在 YUV 平面里，(U,V) 是一个二维向量：角度是色相，长度是饱和度。旋转角度改色相，缩放长度改饱和度，Y 不变。\n\n公式里 `θ` 是色相旋转角，`sat` 是饱和度。",
    "u' = (u cosθ - v sinθ) · sat\nv' = (u sinθ + v cosθ) · sat",
    ["角度转弧度。",
     "逐像素旋转 + 缩放。",
     "U/V clamp [-0.5,0.5]。"],
    "./build/isp_17_hue_saturation out/16_nr_chroma.isp out/17_hue_saturation.isp --sat 1.08 --hue 0",
    ["sat 0.5/1/1.5。",
     "hue ±30°，看肤色。",
     "把 sat 设 0，得到灰度。"],
    ["旋转后不 clamp，U/V 溢出。",
     "只改 R/B 通道，肤色会偏。",
     "在 RGB 里改饱和度，容易过曝。"])

add("18","scale_crop","Scale & Crop：缩放裁剪",
    "最后再缩放，避免中间阶段反复重采样。",
    "f32 YUV 全分辨率", "f32 YUV，1/2 或 1/4 + 可选 16:9",
    ["理解重采样顺序", "知道 box 平均", "会看裁剪构图"],
    "缩放放在最后，避免中间阶段反复重采样。支持 1/2、1/4 整数倍 box 平均：每个输出像素取 2×2/4×4 输入的平均。\n\n`--crop` 会中心裁成 16:9：宽不变，高取 `w*9/16`。",
    "out(x,y) = mean(in(2x..2x+1, 2y..2y+1))\n16:9: h' = w × 9 / 16",
    ["根据 scale 选 1/2/4 倍。",
     "逐输出像素做 box 平均。",
     "可选中心裁剪，复制到新 Image。"],
    "./build/isp_18_scale_crop out/17_hue_saturation.isp out/18_scale_crop.isp --scale 0.5 --crop",
    ["0.5/0.25 对比细节。",
     "`--crop` 与不裁对比构图。",
     "先缩放再锐化，对比顺序反过来。"],
    ["每步都缩放，细节被反复重采样。",
     "裁剪不居中，构图偏。",
     "YUV 的 U/V 单独下采样，颜色错位。"])

add("19","encoder","Encoder：输出 PNG / YUV",
    "YUV→RGB 写 PNG；可选写 YUV420 planar。",
    "f32 YUV", "8bit RGB PNG；可选 YUV420 `.yuv`",
    ["理解 YUV→RGB", "知道 4:2:0 是什么", "会检查输出"],
    "显示器和 PNG 要 RGB，所以最后一步把 YUV 转回 RGB：\n\nR=Y+1.5748V，G=Y-0.1873U-0.4681V，B=Y+1.8556U。\n\n`--yuv` 还会写 YUV420：Y 全分辨率，U/V 各 2×2 下采样，文件大小约为 RGB 的一半。",
    "R = Y + 1.5748V\nG = Y - 0.1873U - 0.4681V\nB = Y + 1.8556U",
    ["逐像素 YUV→RGB，量化到 8bit。",
     "`write_png_rgb8()` 写 PNG。",
     "`--yuv` 时写 Y/U/V 三个平面。"],
    "./build/isp_19_encoder out/18_scale_crop.isp out/final.png --yuv",
    ["看 PNG 和 YUV 的文件大小。",
     "用 ffmpeg 读 YUV420，确认格式。",
     "对比 `--yuv` 与不写的输出。"],
    ["YUV→RGB 系数和前面 RGB→YUV 不互逆，颜色会偏。",
     "U/V 没减 0.5 就量化，颜色整体偏。",
     "YUV420 的宽高不是偶数，平面大小算错。"])

EXTRA = [
dict(why="没有这一步，后面的坐标、CFA、黑白电平全是猜的。纯 `.raw` 不像 PNG 自带文件头，meta 就是它的“身份证”。", q=["把 width 改错 1，程序会报什么？", "为什么 meta 不直接塞进 .raw 头部？", "RGGB 和 BGGR 的差别会在哪一步暴露？"]),
dict(why="黑电平是加性偏置，必须在任何乘性增益之前处理；否则白平衡会把偏置一起放大，暗部出现固定偏色。", q=["black 写 0 会怎样？", "为什么四个 CFA 位置要分开减？", "clip 与不 clip 分别适合什么场景？"]),
dict(why="暗角是光学系统的乘性衰减，越靠后处理，越容易把噪声一起放大。放在 RAW 域、去马赛克之前，增益只作用在一次采样上。", q=["为什么四角增益大于 1？", "没有 flat-field 时，场景内容会怎样污染估计？", "强度 1 为什么会放大四角噪声？"]),
dict(why="坏点在 RAW 域只是一个像素；去了马赛克，它会参与邻居插值，扩散成 3×3 的彩色斑块，再也回不去。", q=["hot pixel 和 dead pixel 的读数有什么不同？", "阈值太大会漏修什么？", "为什么只用同色邻居？"]),
dict(why="RAW 域噪声是“单通道、线性”的，模型最简单；去马赛克后噪声会变成彩色斑块，再降噪就容易糊掉颜色边界。", q=["光子噪声和读出噪声随信号如何变化？", "σ_range 过大会发生什么？", "为什么只采样同色邻居？"]),
dict(why="白平衡是乘性增益，必须放在去马赛克之前：Bayer 上每个像素只有一种颜色，乘增益不会引入插值误差；放到后面反而会把插值误差一起放大。", q=["灰度世界在什么场景会失败？", "为什么 G 增益固定为 1？", "AsShotNeutral 与 RGB 增益如何互换？"]),
dict(why="去马赛克是 RAW 域和 RGB 域的分界：输入单通道 Bayer，输出三通道 RGB。它必须在白平衡之后、颜色校正之前。", q=["为什么 G 的采样率是 R/B 的两倍？", "双线性和 MHC 的伪彩差在哪？", "为什么边界要用双线性兜底？"]),
dict(why="去马赛克后噪声变成彩色斑块，但人眼对色度分辨率低，所以先在 RGB 域把色度压掉，避免后面 CCM 把色度噪声放大。", q=["为什么只降 U/V 不降 Y？", "中值滤波对彩色噪点为什么有效？", "强度 1 为什么会渗色？"]),
dict(why="串扰是 CFA 光谱响应造成的，属于“相机色彩空间”的问题；必须在 CCM 之前校正，否则 CCM 会把串扰当成颜色偏差一起拟合。", q=["串扰和 CCM 的区别是什么？", "为什么行归一化能保住白点？", "k 过大会发生什么？"]),
dict(why="CCM 是“相机 RGB → sRGB”的核心线性变换，必须在 Gamma 之前；Gamma 之后数据不再线性，矩阵乘法就不成立。", q=["cam_to_xyz 的方向是哪边到哪边？", "负系数为什么放大噪声？", "行归一化的几何意义是什么？"]),
dict(why="高光压缩必须在 Gamma 之前：Gamma 会把 >1 的部分压到 1 附近，先做就无法区分“真正的高光”和“已经饱和的通道”。", q=["硬 clip 为什么会产生品红？", "k 越大画面为什么越灰？", "WDR 和多帧 HDR 的区别？"]),
dict(why="Gamma 是线性光到显示编码的边界；它必须在 CCM、WDR 之后，Color Space 之前。提前做 Gamma，后面的线性矩阵全部失效。", q=["sRGB 为什么在暗部有一段线性？", "自动曝光用均值为什么会失败？", "手动 EV 与曝光时间的关系？"]),
dict(why="YUV 是 RGB 域和 YUV 域的分界：之后所有增强都在 Y/U/V 上做，不再反复转 RGB。", q=["为什么 U/V 可以是负的？", "BT.709 和 BT.601 的差别？", "full range 与 limited range 的差别？"]),
dict(why="Y 承载细节，降噪要在“细节”和“噪声”之间取舍；放在 YUV 域，U/V 已经分离，不会把色度一起糊掉。", q=["σ 太大会发生什么？", "为什么只改 channel 0？", "双边和普通高斯的差别？"]),
dict(why="锐化放在降噪之后：先降噪，避免把噪声放大；只锐化 Y，避免彩色描边。", q=["unsharp mask 的“半径”由什么决定？", "阈值的作用是什么？", "为什么不在 RAW 域锐化？"]),
dict(why="对比度/亮度是显示端操作，放在 YUV 域只改 Y，色相不变；放在 RGB 域会让饱和度一起变。", q=["对比度 2 为什么会死黑？", "brightness 与曝光的关系？", "为什么只改 Y？"]),
dict(why="色度降噪放在亮度处理之后：此时 Y 已经稳定，U/V 可以更激进地中值，不会影响亮度细节。", q=["中值窗口为什么是 3×3？", "强度 1 为什么会渗色？", "和 stage 07 的区别？"]),
dict(why="色相/饱和度是最后的颜色创作步骤；放在 YUV 域，Y 不变，肤色/天空可以单独改。", q=["色相旋转多少度会互补？", "饱和度 0 会得到什么？", "为什么在 YUV 里做比 RGB 好？"]),
dict(why="缩放放最后，避免中间阶段反复重采样；裁剪也放最后，先处理完整画面，避免边界效应。", q=["box 平均和双线性缩放的差别？", "为什么先缩放后锐化会不同？", "16:9 裁剪会丢多少像素？"]),
dict(why="编码是“数据 → 文件”的边界：之前都是浮点线性/显示数据，最后才量化成 8bit，并可选 4:2:0 压缩色度。", q=["YUV420 的 U/V 为什么只有 1/4 大小？", "量化误差会出现在哪里？", "PNG 与 YUV 的用途差别？"]),
]

NAMES = [x["title"].split("：")[0] for x in D]
for i, x in enumerate(D):
    prev = f"[Stage {i-1:02d} · {D[i-1]['title'].split('：')[0]}](../{D[i-1]['num']}_{D[i-1]['d']}/README.md)" if i else "无"
    nxt = f"[Stage {i+1:02d} · {D[i+1]['title'].split('：')[0]}](../{D[i+1]['num']}_{D[i+1]['d']}/README.md)" if i < 19 else "[课程首页](../../README.md)"
    img = f"compare_{i:02d}.png" if i else "stage_00.png"
    cap = "左：上一阶段；右：本阶段。同一张 `.raw`，同一次流水线。" if i else "stage 00 读进来的单通道 Bayer；下面补充它的 2×2 排列。"
    extra_img = "" if i else "![bayer](../../docs/images/bayer_pattern.png)\n\n*RGGB：G 占 50%，R/B 各 25%。*\n"
    goals = "\n".join(f"- {g}" for g in x["goals"])
    text = f'''# Stage {x['num']} · {x['title']}

> **一句话**：{x['short']}

## 前后对比

![stage {x['num']}](../../docs/images/{img})

*{cap}*

{extra_img}

---

## 本节目标

{goals}

## 输入 / 输出

| | |
|---|---|
| 输入 | {x['inp']} |
| 输出 | {x['outp']} |
| 目录 | `stages/{x['num']}_{x['d']}/` |

## 原理

{x['principle']}

### 公式

```text
{x['formula']}
```

## 代码走读

文件：[`stages/{x['num']}_{x['d']}/stage.cpp`](stage.cpp)

{chr(10).join(f"{j+1}. {c}" for j, c in enumerate(x['code']))}

## 跑一跑

```bash
{x['cmd']}
```

## 观察与实验

{chr(10).join(f"- {e}" for e in x['exp'])}

## 常见坑

{chr(10).join(f"- {p}" for p in x['pitfall'])}

## 为什么放在这个位置

{EXTRA[i]['why']}

## 自检

{chr(10).join(f"- {q}" for q in EXTRA[i]['q'])}

---

**上一节** → {prev}  
**下一节** → {nxt}
'''
    Path(f"stages/{x['num']}_{x['d']}/README.md").write_text(text, encoding="utf-8")
print("wrote", len(D))
