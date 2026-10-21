#!/usr/bin/env python3
"""根据 tools/script_text.py 和已经生成的配音，重新生成 docs/PPT_讲解词.md。

用法：
    python3 tools/make_script_doc.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_video as mv

TITLES = [
    "封面：从 .raw 到 RGB",
    "问题：.raw 不是图片",
    "全景：20 个 stage / 三个域",
    "RAW 域：先修传感器和镜头",
    "去马赛克：猜颜色",
    "RGB 域：颜色、动态范围、Gamma",
    "YUV 域：修观感，再编码",
    "工程：一个 stage 一个目录",
    "结果：2880×1620 / 13 秒",
    "总结与 Q&A",
]
VISUALS = [
    "深蓝底，右侧最终成片。",
    "左边三条要点，右边 Bayer 色块图。",
    "三域流程图：RAW 7 步、RGB 6 步、YUV 7 步。",
    "左 RAW 直方图，右 6 个 RAW 阶段。",
    "左双线性 / 右 MHC 的 100% 对比。",
    "左 CCM 后结果，右 6 个 RGB 阶段。",
    "左 RGB→YUV 结果，右 6 个 YUV 阶段。",
    "左侧代码目录，右侧三张卡片。",
    "最终成片 + 20/13s/0 diff/2.9K。",
    "深蓝底，三条总结。",
]
ACTIONS = [
    "说到 20 个 stage 时指橙色小字。",
    "说到 Bayer 时指右边色块。",
    "用手从上排划到下排，强调三域。",
    "指直方图黑电平线，再指右侧 BLC。",
    "指左图边缘伪彩，再指右图。",
    "指 CCM 结果，再指右列。",
    "指 YUV 结果，再指右列。",
    "指 stages/06_demosaic/ 目录。",
    "四个数字依次点。",
    "说完谢谢停住。",
]


def pretty(t):
    sents = [x for x in re.split(r"(?<=[。！？])", t) if x.strip()]
    return "\n>\n> ".join(x.strip() for x in sents)


def ts(t):
    m = int(t // 60)
    s = int(round(t % 60))
    if s == 60:
        m += 1
        s = 0
    return f"{m}:{s:02d}"


def main():
    if len(mv.TEXTS) != len(TITLES):
        raise SystemExit(
            f"TEXTS 有 {len(mv.TEXTS)} 页，但 PPT_讲解词 的模板是 {len(TITLES)} 页；"
            "加页/删页时请同步修改 tools/make_script_doc.py 和 tools/make_ppt.py"
        )

    durs, starts, total = [], [], 0.0
    for i in range(1, len(mv.TEXTS) + 1):
        mp3 = mv.AUDIO / f"slide_{i:02d}.mp3"
        if not mp3.exists():
            raise SystemExit(f"缺少 {mp3}，请先运行 python3 tools/make_video.py")
        d = mv.media_duration(mp3) + mv.TAIL
        starts.append(total)
        durs.append(d)
        total += d

    out = ["# 《从 RAW 到 RGB》5 分钟讲解词（视频版）\n"]
    out.append(
        "> 配套视频：[ISP_Raw_5min.mp4](ISP_Raw_5min.mp4) · "
        "[字幕 SRT](subtitles/ISP_Raw_5min.srt)  \n"
        "> 演示文稿：[ISP_Raw_5min.pptx](ISP_Raw_5min.pptx) · "
        "[PDF 备份](ISP_Raw_5min.pdf)  \n"
        f"> 配音：`{mv.VOICE}`，语速 `{mv.RATE}`，音高 `{mv.PITCH}`；"
        f"全片 **{ts(total)}**。\n>\n"
        "> 原则：**不要念幻灯片上的字**，讲“为什么”和“我做了什么”。"
        "本文与视频里的实际配音逐句一致。\n"
    )
    out.append("---\n## 时间分配\n")
    out.append("| 页码 | 内容 | 时长 | 时间轴 |\n|------|------|------|--------|")
    for i in range(len(mv.TEXTS)):
        out.append(
            f"| {i + 1} | {TITLES[i]} | {durs[i]:.0f}s | "
            f"{ts(starts[i])}–{ts(starts[i] + durs[i])} |"
        )
    out.append(
        f"\n> 全片总长 **{ts(total)}**。如果现场只剩 4 分钟：删掉第 8 页“工程”，"
        "第 4、5、6 页各压 10 秒。\n\n---\n"
    )

    for i in range(len(mv.TEXTS)):
        out.append(
            f"## 第 {i + 1} 页 · {TITLES[i]}"
            f"（{ts(starts[i])}–{ts(starts[i] + durs[i])}）\n\n"
            f"**画面**：{VISUALS[i]}\n\n**讲稿**：\n\n"
            f"> {pretty(mv.TEXTS[i])}\n\n**动作**：{ACTIONS[i]}\n\n---\n"
        )

    out.append('''## 附：可能被问到的问题

**Q1：为什么不用 OpenCV / LibRaw？**
> 因为教学目标是“看见 RAW 长什么样”。LibRaw 会把解析细节藏起来；
> 我们用一个 500 行的最小 DNG 解析器，把 IFD、CFA、黑电平都摊开。
> 真实产品当然应该用 LibRaw/rawspeed。

**Q2：为什么 LSC 的效果看起来一般？**
> 这张图用的是“从图像自身统计估计暗角”，没有 flat-field 标定，
> 场景内容会污染估计。工业上必须用均匀白板标定，这也是 stage 02
> 讲义里专门讲的局限。

**Q3：为什么没有 HDR、3A、镜头畸变？**
> 这是 5 分钟能讲完的最小闭环：RAW → RGB。3A、HDR、畸变校正、
> 色度降噪都是下一步；PRINCIPLES.md 最后一章列了完整的“从教学到产品”清单。

**Q4：为什么去马赛克放在白平衡之后？**
> Bayer 上每个像素只有一种颜色，先乘增益不会引入插值误差；
> 而且白平衡是线性运算，放在去马赛克之前更符合“RAW 域做修复”的原则。

**Q5：9 秒是不是太慢了？**
> 这是单线程、教学优先的实现，PNG 压缩还占了 5~6 秒。
> 量产 ISP 会用 SIMD/GPU、tile 处理、零拷贝，速度是另一个数量级。

---

## 附：放映/发布前检查清单

- [ ] 视频：`docs/ISP_Raw_5min.mp4`，1920×1080，30fps；
- [ ] 字幕：`docs/subtitles/ISP_Raw_5min.srt`，可单独挂载；
- [ ] PPT：`docs/ISP_Raw_5min.pptx`，10 页，含演讲者备注；
- [ ] PDF：`docs/ISP_Raw_5min.pdf`，10 页，放映备份；
- [ ] 若现场演示：提前 `./build.sh`，并跑一次 `./run_pipeline.sh` 确认 9 秒。
''')

    path = mv.DOCS / "PPT_讲解词.md"
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {path}  ({ts(total)})")


if __name__ == "__main__":
    main()
