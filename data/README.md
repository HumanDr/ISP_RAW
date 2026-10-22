# 示例 RAW 数据

| 文件 | 说明 |
|------|------|
| `sample.raw` | 5760×3840，16bit little-endian，无文件头，RGGB Bayer |
| `sample.meta` | 宽高、CFA、黑/白电平、白平衡、颜色矩阵 |

`sample.raw` 来自一张真实相机的未压缩 DNG：
Canon EOS 5D Mark III，Canon 5D3 的 Bayer 数据被原样导出为纯 `.raw`。
原始 DNG 来自 [raw.pixls.us](https://raw.pixls.us/)，CC0，作者 Simon Harhues，
MD5 `369ad95edaf2c7fcaab11c3cb71eeb9b`。

## 为什么用 .raw + .meta

纯 `.raw` 只有像素，没有宽高/CFA/黑电平，ISP 无法解释它。
工业上这些信息可能在传感器寄存器、驱动、或 DNG/EXIF 里；教学工程把它
显式写在 `.meta` 中，方便你手改参数做实验。

`sample.raw` 可以用 `xxd` 直接看：

```bash
xxd -l 32 data/sample.raw
```

前两个 16bit 就是 Bayer 左上角的 R/G 像素。

---

## 新增：风景示例 `landscape.raw`（不覆盖 `sample.raw`）

| 文件 | 说明 |
|---|---|
| `landscape.raw` | 3088×2056，16bit little-endian，RGGB Bayer |
| `landscape.meta` | 黑电平 127/127/126/127，白电平 4000，Canon EOS D60 |
| `landscape_full.crw` | 原始 CRW 样本，仅作来源存档 |

来源：[raw.pixls.us](https://raw.pixls.us/) 的 **Canon EOS D60 RAW (3:2)**，
样本编号 2010，CC0。`landscape.raw` 是用 rawpy 从 CRW 的
`raw_image_visible` 直接导出的真实 Bayer 数据，不是从 RGB 反推的。

```bash
./build/isp_pipeline \
  --raw data/landscape.raw --meta data/landscape.meta \
  --out out/landscape/final.png
```

输出 1544×868（1/2 缩放 + 16:9 裁剪），单线程约 3 秒。
`data/sample.raw` / `sample.meta` 仍然保留，未覆盖。
