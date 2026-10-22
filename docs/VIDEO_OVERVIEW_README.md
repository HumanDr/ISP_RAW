# 通用 ISP 科普动画

> 成片：[`ISP_Overview_Animated.mp4`](ISP_Overview_Animated.mp4)  
> 字幕：[`subtitles/ISP_Overview_Animated.srt`](subtitles/ISP_Overview_Animated.srt) ·
> [`ISP_Overview_Animated.ass`](ISP_Overview_Animated.ass)  
> 封面：[`images/isp_overview_poster.jpg`](images/isp_overview_poster.jpg)

![poster](images/isp_overview_poster.jpg)

## 定位

这条视频**不讲任何具体工程**，只讲 ISP 本身：

1. ISP 是什么，为什么 RAW 不是图片；
2. 传感器、Bayer、ADC、RAW 的关系；
3. 典型 ISP 的三段流水线：RAW 域、RGB 域、YUV 域；
4. 每一段在修什么、原理是什么、顺序为什么不能乱；
5. 3A 控制闭环；
6. 手机/汽车/安防/医疗等应用。

## 规格

| 项目 | 值 |
|---|---|
| 时长 | **6:46** |
| 开场 | 前 **2 秒**只停讲解，音乐和动画继续 |
| 画面 | 1920×1080，24fps，H.264 High |
| 声音 | AAC 48kHz 立体声；Xiaoyi，`+2%` / `+2Hz` |
| 字幕 | 米色衬线 + 深色描边，烧录；另附 SRT |
| 音乐 | numpy 合成的 Am–F–C–G 氛围铺底，低音量 |
| 体积 | 约 32 MB |

## 分镜

| # | 场景 | 内容 |
|---|------|------|
| 1 | ISP 是什么 | ISP 中文含义；光 → 镜头 → 传感器 → RAW → 照片 |
| 2 | RAW 的原始语言 | Bayer 马赛克、位深、元数据、低对比 |
| 3 | 三段旅程 | RAW/RGB/YUV 三段节点逐段点亮 |
| 4 | RAW 域 | BLC 直方图、LSC 暗角、DPC 邻域、NR、AWB、Demosaic |
| 4 | 去马赛克 | 同一区域放大，双线性 / MHC / 逐像素差异图 |
| 6 | RGB 域 | 色度降噪、串扰、CCM、HDR、Gamma、RGB→YUV |
| 7 | YUV 域 | Y/U/V、亮度降噪/锐化、420、输出 |
| 8 | 3A | AE/AF/AWB 的测量与反馈 |
| 9 | 顺序 | 加性/乘性、Gamma、去马赛克顺序 |
| 10 | 应用与总结 | 手机/汽车/安防/医疗，三句话总结 |

逐句讲稿：[`ISP_Overview_讲解词.md`](ISP_Overview_讲解词.md)。

## 示例画面

风景示例来自 [raw.pixls.us](https://raw.pixls.us/) 的 **Canon EOS D60 RAW (3:2)** 样本：
- 许可：CC0；
- 文件：`CRW_0099.CRW`，样本编号 2010；
- 视频里的 RAW / RGB / YUV 画面来自 `docs/images/landscape/stage_*.png` 的实际 C++ 工程输出；Bayer 网格只是把 RAW 的 2×2 排列可视化。

这样既有真实 RAW 的风景，又能把“RAW 长什么样”讲清楚。

## 重新生成

```bash
cd /home/lchin/ISP_Raw_Course

# 1. 改稿：tools/isp_overview_script.py
# 2. 重新配音
PYTHONPATH=.pylibs python3 tools/isp_overview_tts.py

# 3. 重新计算句子边界（字幕精确对齐）
PYTHONPATH=.pylibs python3 tools/isp_overview_bounds.py

# 4. 渲染 + 混音 + 烧字幕
python3 tools/make_isp_overview.py
```

只改字幕时：

```bash
python3 tools/make_isp_overview.py --reburn
```

## 保留的旧视频

- PPT 版：`ISP_Raw_5min.mp4`（5:27）
- RAW 工程动画：`ISP_Raw_Animated_5min.mp4`（5:01）
- 本视频：`ISP_Overview_Animated.mp4`（6:46）

三者互不覆盖。
