#!/usr/bin/env python3
"""用 LibreOffice UNO 生成 5 分钟讲解 PPT（pptx + pdf）。

运行方式（脚本会自己拉起 headless soffice）：
    python3 tools/make_ppt.py
"""
import os
import subprocess
import time
from pathlib import Path

import uno
from com.sun.star.awt import Point, Size
from com.sun.star.beans import PropertyValue
from PIL import Image

from script_text import TEXTS, TIMES

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "images"
OUT = ROOT / "docs"
PPTX = OUT / "ISP_Raw_5min.pptx"
PDF = OUT / "ISP_Raw_5min.pdf"

W, H = 33867, 19050  # 13.333 x 7.5 in, 1/100 mm
FONT = "Microsoft YaHei"
MONO = "Consolas"

NAVY = 0x0B1F33
INK = 0x0F172A
MUTED = 0x64748B
LIGHT = 0xF7F8FA
WHITE = 0xFFFFFF
BLUE = 0x2563EB
ORANGE = 0xF59E0B
CARD = 0xFFFFFF
BORDER = 0xE2E8F0
DARK_CARD = 0x111C2E
DARK_TEXT = 0xE2E8F0
GREEN = 0x15803D


# PPT 第 2 页用的 Bayer 色块（从 docs/images/bayer_pattern.png 裁出）
_GRID = IMG / "ppt_bayer_grid.png"
if not _GRID.exists():
    _im = Image.open(IMG / "bayer_pattern.png")
    _im.crop((0, 45, 535, 600)).save(_GRID)


def P(x_in, y_in):
    return Point(int(x_in * 2540), int(y_in * 2540))


def S(w_in, h_in):
    return Size(int(w_in * 2540), int(h_in * 2540))


def prop(name, value):
    p = PropertyValue()
    p.Name = name
    p.Value = value
    return p


class Deck:
    def __init__(self, doc):
        self.doc = doc
        self.pages = doc.getDrawPages()

    def page(self, i):
        return self.pages.getByIndex(i)

    def setup(self, n):
        while self.pages.getCount() < n:
            self.pages.insertNewByIndex(self.pages.getCount())
        for i in range(n):
            p = self.pages.getByIndex(i)
            p.Width = W
            p.Height = H

    def rect(self, slide, x, y, w, h, fill, line=None, line_w=1.0):
        s = self.doc.createInstance("com.sun.star.drawing.RectangleShape")
        s.Position = P(x, y)
        s.Size = S(w, h)
        s.FillStyle = 1  # SOLID
        s.FillColor = fill
        if line is None:
            s.LineStyle = 0  # NONE
        else:
            s.LineStyle = 1
            s.LineColor = line
            s.LineWidth = int(line_w * 35)
        slide.add(s)
        return s

    def text(self, slide, x, y, w, h, s, size=16, color=INK, bold=False,
             font=FONT, align=0, valign=0):
        sh = self.doc.createInstance("com.sun.star.drawing.TextShape")
        sh.Position = P(x, y)
        sh.Size = S(w, h)
        slide.add(sh)
        sh.FillStyle = 0
        sh.LineStyle = 0
        sh.TextLeftDistance = 0
        sh.TextRightDistance = 0
        sh.TextUpperDistance = 0
        sh.TextLowerDistance = 0
        sh.TextWordWrap = True
        sh.setString(s)
        sh.CharFontName = font
        sh.CharFontNameAsian = font
        sh.CharHeight = float(size)
        sh.CharHeightAsian = float(size)
        sh.CharColor = color
        sh.CharWeight = 150.0 if bold else 100.0
        sh.CharWeightAsian = 150.0 if bold else 100.0
        sh.ParaAdjust = align
        sh.TextVerticalAdjust = valign
        return sh

    def image(self, slide, path, bx, by, bw, bh, border=True, dark=False):
        iw, ih = Image.open(path).size
        aspect = iw / ih
        if aspect > bw / bh:
            w = bw
            h = bw / aspect
        else:
            h = bh
            w = bh * aspect
        x = bx + (bw - w) / 2
        y = by + (bh - h) / 2
        if border:
            self.rect(slide, x - 0.04, y - 0.04, w + 0.08, h + 0.08,
                      DARK_CARD if dark else WHITE,
                      0x1E293B if dark else BORDER)
        sh = self.doc.createInstance("com.sun.star.drawing.GraphicObjectShape")
        sh.GraphicURL = uno.systemPathToFileUrl(str(path))
        sh.Position = P(x, y)
        sh.Size = S(w, h)
        slide.add(sh)
        return x, y, w, h

    def oval(self, slide, x, y, d, fill):
        s = self.doc.createInstance("com.sun.star.drawing.EllipseShape")
        s.Position = P(x, y)
        s.Size = S(d, d)
        s.FillStyle = 1
        s.FillColor = fill
        s.LineStyle = 0
        slide.add(s)
        return s

    def notes(self, slide, s):
        npage = slide.getNotesPage()
        # index 0 是 slide thumbnail，index 1 是 NotesShape
        shape = npage.getByIndex(1)
        shape.setString(s)
        shape.CharFontName = FONT
        shape.CharFontNameAsian = FONT
        shape.CharHeight = 13.0
        shape.CharHeightAsian = 13.0
        shape.CharColor = 0x334155

    def footer(self, slide, num, total=10, dark=False):
        col = 0x94A3B8 if dark else 0x94A3B8
        self.text(slide, 0.75, 7.12, 4.0, 0.22, "ISP Pipeline · 5 min",
                  size=9, color=col)
        self.text(slide, 11.55, 7.12, 1.03, 0.22, f"{num:02d} / {total:02d}",
                  size=9, color=col, align=1)

    def eyebrow(self, slide, s):
        self.text(slide, 0.75, 0.42, 5.0, 0.25, s, size=11, color=ORANGE,
                  bold=True)

    def title(self, slide, s):
        self.text(slide, 0.75, 0.7, 11.8, 0.75, s, size=28, color=NAVY,
                  bold=True)


def build():
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    ctx = resolver.resolve(
        "uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
    desktop = ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop", ctx)
    doc = desktop.loadComponentFromURL("private:factory/simpress", "_blank", 0, ())
    d = Deck(doc)
    d.setup(10)
    IMG = ROOT / "docs" / "images"

    # 1 封面
    s = d.page(0)
    d.rect(s, 0, 0, 13.333, 7.5, NAVY)
    d.rect(s, 0.75, 1.28, 0.08, 2.1, ORANGE)
    d.text(s, 1.02, 1.15, 6.4, 0.9, "从 .raw 到 RGB", size=38, color=WHITE, bold=True)
    d.text(s, 1.02, 2.12, 6.3, 0.6, "按三域流程手写 ISP Pipeline", size=24, color=0xCBD5E1)
    d.text(s, 1.02, 3.02, 6.3, 0.35, "20 个 stage  ·  5760×3840  ·  约 13 秒",
           size=13, color=ORANGE, bold=True)
    d.text(s, 1.02, 3.65, 5.9, 0.9, "BLC → Demosaic → CCM → Gamma → YUV → PNG",
           size=13, color=0x94A3B8)
    d.image(s, IMG / "final_full.png", 7.15, 0.85, 5.5, 3.75, dark=True)
    d.text(s, 7.15, 4.78, 5.5, 0.3, "输入 .raw + .meta · 输出 RGB PNG",
           size=10, color=0x94A3B8, align=3)
    d.text(s, 1.02, 6.55, 5.0, 0.3, "5 分钟讲解  ·  2026", size=11, color=0x64748B)

    # 2 .raw 不是图片
    s = d.page(1)
    d.rect(s, 0, 0, 13.333, 7.5, LIGHT)
    d.eyebrow(s, "01 / 问题")
    d.title(s, "为什么 .raw 不是一张图片？")
    for i, t in enumerate([
        "只有像素，没有宽高 / CFA / 黑电平",
        "传感器是 Bayer 阵列：每个像素只有 R/G/B 之一",
        "旁边必须有 .meta，ISP 才能解释它",
    ]):
        d.oval(s, 0.78, 1.86 + i * 0.62, 0.1, ORANGE)
        d.text(s, 1.02, 1.76 + i * 0.62, 5.7, 0.45, t, size=15, color=INK)
    d.rect(s, 0.75, 4.1, 5.95, 1.2, DARK_CARD)
    d.text(s, 1.0, 4.3, 5.45, 0.85, "ISP = 把 Bayer 单通道\n变成可显示 RGB 的 20 步",
           size=17, color=WHITE, bold=True)
    d.image(s, IMG / "bayer_pattern.png", 7.0, 1.45, 5.6, 3.0)
    d.text(s, 7.0, 4.62, 5.6, 0.3, "RGGB：G 占 50%，R/B 各占 25%", size=10.5,
           color=MUTED, align=3)
    d.text(s, 7.0, 5.15, 5.6, 0.3, "data/sample.raw + data/sample.meta", size=10.5,
           color=BLUE, bold=True, align=3)
    d.footer(s, 2)

    # 3 全景
    s = d.page(2)
    d.rect(s, 0, 0, 13.333, 7.5, LIGHT)
    d.eyebrow(s, "02 / 全景")
    d.title(s, "20 个 stage，三个域")
    d.image(s, IMG / "pipeline.png", 0.8, 1.35, 11.75, 5.5)
    d.footer(s, 3)

    # 4 RAW 域
    s = d.page(3)
    d.rect(s, 0, 0, 13.333, 7.5, LIGHT)
    d.eyebrow(s, "03 / RAW 域")
    d.title(s, "先修传感器和镜头")
    d.image(s, IMG / "raw_histogram.png", 0.75, 1.55, 6.15, 3.0)
    d.text(s, 0.75, 4.65, 6.15, 0.28, "黑电平 2047 · 白电平 15000 · 16 bit",
           size=10.5, color=MUTED, align=3)
    d.rect(s, 0.75, 5.05, 6.15, 0.95, DARK_CARD)
    d.text(s, 0.98, 5.2, 5.7, 0.6, "先减黑电平，再乘增益。\n否则暗部会被放大成偏色。",
           size=12.5, color=WHITE, bold=True)
    rows = [("01", "BLC", "黑电平"), ("02", "LSC", "镜头阴影"),
            ("03", "BPC/DPC", "坏点"), ("04", "NR RAW", "RAW 降噪"),
            ("05", "AWB", "自动白平衡"), ("06", "Demosaic", "颜色插值")]
    y = 1.55
    for num, name, desc in rows:
        d.oval(s, 7.35, y + 0.03, 0.38, ORANGE)
        d.text(s, 7.35, y + 0.075, 0.38, 0.2, num, size=9, color=WHITE, bold=True, align=3)
        d.text(s, 7.9, y - 0.02, 4.6, 0.3, name, size=12.5, color=NAVY, bold=True)
        d.text(s, 7.9, y + 0.28, 4.6, 0.3, desc, size=10, color=MUTED)
        y += 0.72
    d.footer(s, 4)

    # 5 Demosaic
    s = d.page(4)
    d.rect(s, 0, 0, 13.333, 7.5, LIGHT)
    d.eyebrow(s, "04 / 去马赛克")
    d.title(s, "每个像素只有一个颜色，怎么变成 RGB？")
    d.image(s, IMG / "demosaic_compare.png", 0.75, 1.5, 7.25, 3.2)
    d.text(s, 0.75, 4.82, 7.25, 0.28, "100% 裁切：左双线性，右 MHC", size=10.5,
           color=MUTED, align=3)
    d.rect(s, 0.75, 5.3, 7.25, 0.95, DARK_CARD)
    d.text(s, 0.98, 5.44, 6.85, 0.6, "G = (G左+G右+G上+G下)/4\nMHC：5×5 卷积 + 梯度修正",
           size=11.5, color=DARK_TEXT)
    d.text(s, 8.35, 1.55, 4.3, 0.3, "双线性", size=14, color=BLUE, bold=True)
    d.text(s, 8.35, 1.9, 4.3, 0.7, "邻居平均，快；\n边缘拉链纹、伪彩。", size=11)
    d.text(s, 8.35, 2.95, 4.3, 0.3, "Malvar-He-Cutler", size=14, color=GREEN, bold=True)
    d.text(s, 8.35, 3.3, 4.3, 0.7, "梯度修正，伪彩更少；\n本课默认。", size=11)
    d.footer(s, 5)

    # 6 RGB 域
    s = d.page(5)
    d.rect(s, 0, 0, 13.333, 7.5, LIGHT)
    d.eyebrow(s, "05 / RGB 域")
    d.title(s, "颜色、动态范围、Gamma")
    d.image(s, IMG / "stage_09.png", 0.75, 1.55, 6.2, 3.1)
    d.text(s, 0.75, 4.78, 6.2, 0.28, "CCM 后：linear sRGB", size=10.5, color=MUTED, align=3)
    rows = [("07", "NR Color", "色度降噪"), ("08", "X-talking", "串扰校正"),
            ("09", "Color Corr.", "相机→sRGB"), ("10", "HDR/WDR", "高光压缩"),
            ("11", "Gamma", "曝光+sRGB"), ("12", "Color Space", "RGB→YUV")]
    y = 1.55
    for num, name, desc in rows:
        d.oval(s, 7.4, y + 0.03, 0.38, ORANGE)
        d.text(s, 7.4, y + 0.075, 0.38, 0.2, num, size=9, color=WHITE, bold=True, align=3)
        d.text(s, 7.95, y - 0.02, 4.6, 0.3, name, size=12.5, color=NAVY, bold=True)
        d.text(s, 7.95, y + 0.28, 4.6, 0.3, desc, size=10, color=MUTED)
        y += 0.72
    d.footer(s, 6)

    # 7 YUV 域
    s = d.page(6)
    d.rect(s, 0, 0, 13.333, 7.5, LIGHT)
    d.eyebrow(s, "06 / YUV 域")
    d.title(s, "最后修观感，再编码")
    d.image(s, IMG / "stage_12.png", 0.75, 1.55, 6.2, 3.1)
    d.text(s, 0.75, 4.78, 6.2, 0.28, "RGB→YUV 之后：Y/U/V 三通道", size=10.5,
           color=MUTED, align=3)
    rows = [("13", "NR Luma", "亮度降噪"), ("14", "Edge Enhance", "边缘增强"),
            ("15", "Contrast", "对比度"), ("16", "NR Chroma", "色度降噪"),
            ("17", "Hue/Sat", "色相饱和"), ("18/19", "Scale/Encoder", "缩放/编码")]
    y = 1.55
    for num, name, desc in rows:
        d.oval(s, 7.4, y + 0.03, 0.38, ORANGE)
        d.text(s, 7.4, y + 0.075, 0.38, 0.2, num, size=8.5, color=WHITE, bold=True, align=3)
        d.text(s, 7.95, y - 0.02, 4.6, 0.3, name, size=12.5, color=NAVY, bold=True)
        d.text(s, 7.95, y + 0.28, 4.6, 0.3, desc, size=10, color=MUTED)
        y += 0.72
    d.footer(s, 7)

    # 8 工程
    s = d.page(7)
    d.rect(s, 0, 0, 13.333, 7.5, LIGHT)
    d.eyebrow(s, "07 / 工程")
    d.title(s, "为什么这套代码适合学？")
    d.rect(s, 0.75, 1.55, 6.35, 4.35, DARK_CARD)
    d.text(s, 1.02, 1.78, 5.8, 4.0,
           "stages/06_demosaic/\n"
           "  README.md    theory\n"
           "  stage.cpp    algorithm\n"
           "  main.cpp     CLI\n"
           "\n"
           "common/\n"
           "  raw.cpp      .raw + .meta\n"
           "  image.h      .isp container\n"
           "  color.h      sRGB / matrix\n"
           "\n"
           "data/\n"
           "  sample.raw\n"
           "  sample.meta",
           size=12, color=DARK_TEXT, font=MONO)
    cards = [("一个 stage 一个函数", "接口在 stages.h，改完再编译。"),
             ("中间格式可检查", ".isp 带头信息，isp_dump 随时看。"),
             ("两种跑法", "内存流水线或 --steps 分步。")]
    y = 1.55
    for name, desc in cards:
        d.rect(s, 7.45, y, 5.15, 1.4, WHITE, BORDER)
        d.text(s, 7.7, y + 0.18, 4.65, 0.3, name, size=13, color=NAVY, bold=True)
        d.text(s, 7.7, y + 0.62, 4.65, 0.55, desc, size=10.5, color=MUTED)
        y += 1.62
    d.text(s, 0.75, 6.1, 6.35, 0.3, "一个目录 = 一节实验课", size=11,
           color=ORANGE, bold=True)
    d.text(s, 7.45, 6.55, 5.15, 0.3, "改算法 → 再编译 → 13 秒看到结果", size=10.5,
           color=ORANGE, bold=True, align=3)
    d.footer(s, 8)

    # 9 结果
    s = d.page(8)
    d.rect(s, 0, 0, 13.333, 7.5, LIGHT)
    d.eyebrow(s, "08 / 结果")
    d.title(s, "跑通：2880×1620，约 13 秒")
    d.image(s, IMG / "final_full.png", 0.75, 1.45, 7.55, 5.2)
    d.text(s, 0.75, 6.78, 7.55, 0.25, "out/final.png  ·  sRGB PNG", size=9.5,
           color=MUTED, align=3)
    stats = [("20", "个 stage", ORANGE), ("13", "秒 / 全流程", BLUE),
             ("0", "分步 vs 内存差异", GREEN), ("2.9K", "×1.6K 输出", NAVY)]
    y = 1.45
    for big, small, col in stats:
        d.rect(s, 8.75, y, 3.85, 1.05, WHITE, BORDER)
        d.text(s, 8.98, y + 0.12, 1.6, 0.5, big, size=24, color=col, bold=True)
        d.text(s, 10.2, y + 0.36, 2.2, 0.3, small, size=10.5, color=MUTED)
        y += 1.25
    d.text(s, 8.75, 6.5, 3.85, 0.3, "同一份 .raw，两种输出", size=9.5, color=MUTED, align=3)
    d.footer(s, 9)

    # 10 总结
    s = d.page(9)
    d.rect(s, 0, 0, 13.333, 7.5, NAVY)
    d.text(s, 0.85, 0.75, 11.6, 0.5, "把三域拆开，ISP 就不再是黑魔法", size=30,
           color=WHITE, bold=True)
    items = [("01", "RAW 域修数据", "BLC、LSC、DPC、NR、AWB、Demosaic"),
             ("02", "RGB 域修颜色", "NR Color、X-talking、CCM、WDR、Gamma"),
             ("03", "YUV 域修观感", "亮度/色度降噪、边缘、对比度、Hue/Sat")]
    y = 2.05
    for num, name, desc in items:
        d.text(s, 0.85, y - 0.05, 0.65, 0.5, num, size=16, color=ORANGE, bold=True)
        d.text(s, 1.55, y - 0.08, 5.5, 0.4, name, size=17, color=WHITE, bold=True)
        d.text(s, 1.55, y + 0.35, 5.5, 0.35, desc, size=11, color=0x94A3B8)
        y += 1.05
    d.rect(s, 0.85, 5.55, 7.9, 0.75, ORANGE)
    d.text(s, 1.05, 5.7, 7.5, 0.4, "先跑通  →  再拆开  →  最后替换算法",
           size=13, color=NAVY, bold=True, align=3)
    d.text(s, 9.35, 2.0, 3.35, 0.8, "谢谢", size=34, color=WHITE, bold=True)
    d.text(s, 9.38, 2.92, 3.2, 0.35, "欢迎提问 / 一起改代码", size=12, color=0x94A3B8)
    d.text(s, 9.38, 3.6, 3.2, 0.3, "docs/PRINCIPLES.md", size=10, color=ORANGE, font=MONO)
    d.footer(s, 10, dark=True)

    for i, t in enumerate(TEXTS):
        d.notes(d.page(i), f"[约 {TIMES[i]} 秒]\n{t}")

    doc.getDocumentProperties().Title = "从 .raw 到 RGB：三域 ISP Pipeline"
    doc.getDocumentProperties().Author = "ISP 教学工程"
    doc.getDocumentProperties().Subject = "5 分钟讲解"
    doc.storeToURL(uno.systemPathToFileUrl(str(PPTX)),
                   (prop("FilterName", "Impress MS PowerPoint 2007 XML"),
                    prop("Overwrite", True)))
    doc.storeToURL(uno.systemPathToFileUrl(str(PDF)),
                   (prop("FilterName", "impress_pdf_Export"),
                    prop("Overwrite", True)))
    doc.close(True)
    print("saved", PPTX)
    print("saved", PDF)


def main():
    # 启动 headless soffice，生成完再关掉
    profile = ROOT / ".lo_profile"
    profile.mkdir(exist_ok=True)
    cmd = [
        "soffice",
        f"-env:UserInstallation=file://{profile}",
        "--headless", "--invisible", "--norestore", "--nologo",
        "--accept=socket,host=127.0.0.1,port=2002;urp;",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            time.sleep(0.25)
            try:
                build()
                return
            except Exception as e:
                if "Connection refused" in str(e) or "NoConnectException" in str(e):
                    continue
                raise
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
