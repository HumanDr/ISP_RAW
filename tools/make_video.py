#!/usr/bin/env python3
"""把 10 页 PPT 变成 5 分钟讲解视频（配音 + 字幕）。

依赖（已安装到 .pylibs，可用 tools/setup_video_env.sh 重建）：
  edge-tts       微软 Edge 在线中文神经语音
  imageio-ffmpeg 自带 ffmpeg 7 静态二进制

用法：
    python3 tools/make_video.py            # 有缓存则复用音频
    python3 tools/make_video.py --force    # 重新配音、重新编码

改稿子请编辑 tools/script_text.py 的 TEXTS（不是 docs/PPT_讲解词.md；
那个 md 是 make_script_doc.py 生成出来的）。
"""
import argparse
import hashlib
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "docs" / "ISP_Raw_5min.pdf"
DOCS = ROOT / "docs"
SUB_DIR = DOCS / "subtitles"
WORK = ROOT / "out" / "video"
SLIDES = WORK / "slides"
AUDIO = WORK / "audio"
SEGS = WORK / "segments"
PYLIBS = ROOT / ".pylibs"

VOICE = "zh-CN-XiaoyiNeural"
RATE = "-8%"
PITCH = "-5Hz"
TAIL = 0.70          # 每页语音后留 0.7 秒，翻页不仓促
FPS = 30
W, H = 1920, 1080

# 讲稿：10 页，和 PPT 的演讲者备注一致（视频版语速稍慢）
from script_text import TEXTS



def find_ffmpeg():
    p = shutil.which("ffmpeg")
    if p:
        return p
    cands = sorted(PYLIBS.glob("imageio_ffmpeg/binaries/ffmpeg-*"))
    if cands:
        return str(cands[0])
    raise SystemExit("找不到 ffmpeg：请先运行 tools/setup_video_env.sh")


FFMPEG = find_ffmpeg()
ENV = dict(os.environ, PYTHONPATH=str(PYLIBS))


def run(cmd, **kw):
    kw.setdefault("stdout", subprocess.PIPE)
    kw.setdefault("stderr", subprocess.PIPE)
    kw.setdefault("text", True)
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r


def media_duration(path):
    out = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)],
                         capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    if not m:
        raise RuntimeError(f"读不出时长: {path}")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def tts_normalize(t):
    # 让 TTS 读得更自然；字幕仍显示原文
    repl = [
        ("→", "到"), ("×", "乘"), ("⁴", "的四次方"),
        ("——", "，"), ("“", ""), ("”", ""),
        ("max diff", "最大差异"),
        ("Malvar-He-Cutler", "Malvar He Cutler"),
        ("MHC", "M H C"),
        ("C++", "C 加加"),
        ("isp_dump", "isp dump"),
    ]
    for a, b in repl:
        t = t.replace(a, b)
    return t


def render_slides():
    SLIDES.mkdir(parents=True, exist_ok=True)
    for i in range(1, len(TEXTS) + 1):
        prefix = SLIDES / f"s{i:02d}"
        for old in SLIDES.glob(f"s{i:02d}-*.png"):
            old.unlink()
        run(["pdftoppm", "-png", "-scale-to-x", str(W), "-scale-to-y", str(H),
             "-f", str(i), "-l", str(i), str(PDF), str(prefix)])
        made = sorted(SLIDES.glob(f"s{i:02d}-*.png"))
        if not made:
            raise RuntimeError(f"第 {i} 页渲染失败")
        dst = SLIDES / f"slide_{i:02d}.png"
        made[0].replace(dst)
        im = Image.open(dst)
        if im.size != (W, H):
            im = im.resize((W, H), Image.LANCZOS)
            im.save(dst)
        print(f"slide {i:02d}: {dst.name}")


def synthesize(i, text, force=False):
    AUDIO.mkdir(parents=True, exist_ok=True)
    stem = AUDIO / f"slide_{i:02d}"
    mp3 = stem.with_suffix(".mp3")
    srt = stem.with_suffix(".srt")
    txt = stem.with_suffix(".txt")
    sig = f"{VOICE}|{RATE}|{PITCH}\n{text}"
    if (not force and mp3.exists() and srt.exists() and txt.exists()
            and txt.read_text(encoding="utf-8") == sig and mp3.stat().st_size > 1000):
        return mp3, srt

    cmd = [sys.executable, "-m", "edge_tts", "--voice", VOICE,
           f"--rate={RATE}", f"--pitch={PITCH}", "--text", tts_normalize(text),
           "--write-media", str(mp3), "--write-subtitles", str(srt)]
    last = ""
    for attempt in range(8):
        r = subprocess.run(cmd, env=ENV, capture_output=True, text=True,
                           timeout=180)
        if r.returncode == 0 and mp3.exists() and mp3.stat().st_size > 1000:
            txt.write_text(sig, encoding="utf-8")
            print(f"tts {i:02d}: {media_duration(mp3):.2f}s")
            return mp3, srt
        last = r.stderr[-300:]
        print(f"tts {i:02d}: 第 {attempt + 1} 次失败，3 秒后重试")
        time.sleep(3)
    raise RuntimeError(f"第 {i} 页配音失败：{last}")


def parse_srt(path):
    text = Path(path).read_text(encoding="utf-8-sig").strip()
    if not text:
        return []
    events = []
    for block in re.split(r"\n\s*\n", text):
        lines = block.splitlines()
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        m = re.match(r"(\d+):(\d+):([\d,]+)\s*-->\s*(\d+):(\d+):([\d,]+)", lines[1])
        if not m:
            continue

        def sec(h, mm, ss):
            return int(h) * 3600 + int(mm) * 60 + float(ss.replace(",", "."))

        content = " ".join(x.strip() for x in lines[2:] if x.strip())
        if content:
            events.append([sec(*m.group(1, 2, 3)), sec(*m.group(4, 5, 6)), content])
    return events


def width_units(s):
    return sum(1.0 if ord(c) > 0x2E80 else 0.55 for c in s)


def split_cues(text, max_units=32):
    # 先按标点切成小句，再把小句拼成不超过 max_units 的字幕块
    clauses = re.findall(r"[^，。！？；：、]*[，。！？；：、]?", text)
    clauses = [c.strip() for c in clauses if c.strip()]
    chunks, cur = [], ""
    for cl in clauses:
        if not cur:
            cur = cl
        elif width_units(cur + cl) <= max_units:
            cur += cl
        else:
            chunks.append(cur)
            cur = cl
    if cur:
        chunks.append(cur)
    # 超长小句硬切
    out = []
    for c in chunks:
        while width_units(c) > max_units:
            acc, cut = "", 0
            for j, ch in enumerate(c):
                acc += ch
                if width_units(acc) > max_units:
                    cut = j
                    break
            out.append(c[:cut])
            c = c[cut:]
        if c:
            out.append(c)
    return out


def wrap_cue(s, max_units=32):
    """按“词”换行，避免把 stage 拆成 sta / ge，也避免标点跑到行首。"""
    tokens = re.findall(r"[A-Za-z0-9_.+\-/%]+|.", s)
    lines, cur = [], ""
    for tok in tokens:
        if not cur:
            cur = tok
        elif width_units(cur + tok) <= max_units or tok in "，。；：！？、":
            cur += tok
        else:
            lines.append(cur)
            cur = tok
    if cur:
        lines.append(cur)
    if len(lines) > 3:
        lines = [lines[0], lines[1], "".join(lines[2:])]
    return "\\N".join(lines)


def build_subtitles(slide_events):
    """slide_events: [(start, [(a,b,text),...]), ...] -> global cues"""
    cues = []
    for start, events in slide_events:
        for a, b, text in events:
            a += start
            b += start
            if b <= a:
                b = a + 0.5
            chunks = split_cues(text)
            if not chunks:
                continue
            weights = []
            for c in chunks:
                w = max(1.0, width_units(c))
                if c[-1] in "。！？":
                    w += 4
                elif c[-1] in "，；：、":
                    w += 1.5
                weights.append(w)
            total_w = sum(weights)
            dur = b - a
            t = a
            for c, w in zip(chunks, weights):
                d = dur * w / total_w
                cues.append([t, t + d, c])
                t += d
    # 去掉极短闪烁，并保证单调
    merged = []
    for c in cues:
        if merged and c[0] - merged[-1][1] < 0.02:
            c[0] = merged[-1][1]
        if c[1] - c[0] < 0.75 and merged:
            merged[-1][1] = max(merged[-1][1], c[1])
            merged[-1][2] += c[2]
        else:
            merged.append(c)
    return merged


def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def write_ass(cues, path):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK SC,36,&H00FFFFFF,&H000000FF,&H00101828,&H80000000,-1,0,0,0,100,100,0.4,0,1,2.0,0,2,80,80,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [head]
    for a, b, text in cues:
        txt = wrap_cue(text).replace("{", "（").replace("}", "）")
        lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Default,,0,0,0,,"
                     f"{{\\fad(80,80)}}{txt}\n")
    path.write_text("".join(lines), encoding="utf-8")


def write_srt(cues, path):
    def ts(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int(round((t - int(t)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    out = []
    for i, (a, b, text) in enumerate(cues, 1):
        out.append(f"{i}\n{ts(a)} --> {ts(b)}\n{text}\n")
    path.write_text("\n".join(out), encoding="utf-8")


def make_segment(i, slide, mp3, dur):
    SEGS.mkdir(parents=True, exist_ok=True)
    seg = SEGS / f"seg_{i:02d}.mp4"
    vf = "[0:v]scale=1920:1080,setsar=1,fps=30,format=yuv420p[v]"
    af = (f"[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
          f"apad=pad_dur={TAIL},atrim=0:{dur:.3f},asetpts=N/SR/TB[a]")
    cmd = [FFMPEG, "-y", "-loop", "1", "-framerate", str(FPS),
           "-i", str(slide), "-i", str(mp3),
           "-filter_complex", f"{vf};{af}",
           "-map", "[v]", "-map", "[a]",
           "-t", f"{dur:.3f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
           "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-movflags", "+faststart", str(seg)]
    run(cmd)
    return seg


def concat(segs, out):
    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in segs), encoding="utf-8")
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
         "-c", "copy", "-movflags", "+faststart", str(out)])


def burn(concat_mp4, ass, srt, total, final):
    filt = (f"drawbox=x=0:y=ih-6:w=iw:h=6:color=0xF59E0B@0.8:t=fill,"
            f"ass={ass.name},"
            f"fade=t=in:st=0:d=0.5,"
            f"fade=t=out:st={max(0, total - 0.6):.2f}:d=1.0")
    cmd = [FFMPEG, "-y", "-i", str(concat_mp4),
           "-vf", filt,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0",
           "-af", "loudnorm=I=-17:TP=-1.5:LRA=11",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-t", f"{total:.3f}",
           "-movflags", "+faststart",
           "-metadata", "title=从 RAW 到 RGB：手写 ISP Pipeline",
           "-metadata", "comment=ISP 教学流水线 · 5 分钟讲解",
           str(final)]
    # ass 滤镜用相对文件名，cwd 设为 WORK
    run(cmd, cwd=WORK)
    shutil.copyfile(WORK / ass.name, DOCS / "ISP_Raw_5min.ass")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="重新配音/编码")
    args = ap.parse_args()

    if not PDF.exists():
        raise SystemExit(f"缺少 {PDF}")
    if not PYLIBS.exists():
        raise SystemExit("缺少 .pylibs：先运行 tools/setup_video_env.sh")

    WORK.mkdir(parents=True, exist_ok=True)
    render_slides()

    slide_events = []
    total = 0.0
    durs = []
    for i, text in enumerate(TEXTS, 1):
        mp3, srt = synthesize(i, text, force=args.force)
        d = media_duration(mp3)
        durs.append(d)
        events = parse_srt(srt)
        # edge-tts 返回的字幕基于“给 TTS 的规范化文本”（C++ 会变成 C 加加），
        # 这里按句号 1:1 换回原始讲稿，保证字幕显示 C++ / 中文标点。
        sents = [x.strip() for x in re.split(r"(?<=[。！？])", text) if x.strip()]
        if len(sents) == len(events):
            events = [(a, b, sents[j]) for j, (a, b, _) in enumerate(events)]
        slide_events.append((total, events))
        total += d + TAIL
        print(f"slide {i:02d}: voice {d:6.2f}s  -> timeline {total:6.2f}s")

    cues = build_subtitles(slide_events)
    ass = WORK / "subs.ass"
    SUB_DIR.mkdir(exist_ok=True)
    srt = SUB_DIR / "ISP_Raw_5min.srt"
    write_ass(cues, ass)
    write_srt(cues, srt)

    segs = []
    for i, (text, d) in enumerate(zip(TEXTS, durs), 1):
        slide = SLIDES / f"slide_{i:02d}.png"
        mp3 = AUDIO / f"slide_{i:02d}.mp3"
        print(f"encode segment {i:02d} ({d + TAIL:.1f}s)")
        segs.append(make_segment(i, slide, mp3, d + TAIL))
    concat_mp4 = WORK / "concat.mp4"
    concat(segs, concat_mp4)

    final = DOCS / "ISP_Raw_5min.mp4"
    print(f"burn subtitles, total {total:.2f}s")
    burn(concat_mp4, ass, srt, total, final)

    print(f"\nDONE  {final}")
    print(f"duration {media_duration(final):.2f}s  "
          f"({int(total // 60)}:{total % 60:05.2f})")
    print(f"subs   {SUB_DIR / 'ISP_Raw_5min.srt'}")


if __name__ == "__main__":
    main()
