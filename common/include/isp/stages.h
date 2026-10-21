// =============================================================================
//  stages.h  --  按“养蝶的庭师”ISP 课程的三域流程重写的 19 个图像处理阶段
//
//  RAW 域（Bayer 单通道）
//    00 raw_load -> 01 BLC -> 02 LSC -> 03 BPC/DPC -> 04 NR RAW
//                -> 05 AWB -> 06 Demosaic
//  RGB 域（三通道，线性/显示空间）
//    07 NR Color -> 08 X-talking -> 09 Color Correction
//                -> 10 HDR/WDR -> 11 Gamma -> 12 Color Space Convert
//  YUV 域（BT.709，Y/U/V 三通道）
//    13 NR Luma -> 14 Edge Enhance -> 15 Contrast/Brightness
//    16 NR Chroma -> 17 Hue/Saturation -> 18 Scale & Crop -> 19 Encoder
// =============================================================================
#pragma once

#include <string>

#include "isp/image.h"

namespace isp {

// 00 读纯 .raw + .meta
void stage00_raw_load(const std::string& raw_path, Image& out,
                      const std::string& meta_path = "");

// 01 黑电平校正
void stage01_blc(Image& img, bool clip = true);

// 02 镜头阴影校正
void stage02_lsc(Image& img, float strength = 0.7f);

// 03 坏点校正
void stage03_dpc(Image& img, float threshold = 0.05f);

// 04 RAW 域降噪
void stage04_nr_raw(Image& img, float sigma_range = 0.f);

// 05 自动白平衡（默认灰度世界；可用 meta 里的 wb 做参考）
void stage05_awb(Image& img, bool gray_world = true, float strength = 1.0f);

// 06 去马赛克
enum class Demosaic { Bilinear, MHC };
void stage06_demosaic(Image& img, Demosaic method = Demosaic::MHC);

// 07 RGB 域色度降噪
void stage07_nr_color(Image& img, float strength = 0.6f);

// 08 颜色串扰校正（X-talking）
void stage08_xtalk(Image& img, float strength = 0.05f);

// 09 颜色校正矩阵
void stage09_color_correction(Image& img, bool normalize_rows = true);

// 10 高光压缩 / 宽动态
void stage10_hdr_wdr(Image& img, float strength = 0.6f);

// 11 自动曝光 + Gamma
void stage11_gamma(Image& img, bool auto_exposure = true, float ev = 0.f);

// 12 RGB -> YUV(BT.709 full range)
void stage12_color_space(Image& img);

// 13 亮度降噪
void stage13_nr_luma(Image& img, float sigma_range = 0.02f);

// 14 边缘增强
void stage14_edge_enhance(Image& img, float amount = 0.5f);

// 15 明度/对比度
void stage15_contrast_brightness(Image& img, float contrast = 1.0f,
                                 float brightness = 0.f);

// 16 色度降噪
void stage16_nr_chroma(Image& img, float strength = 0.6f);

// 17 色调 / 饱和度
void stage17_hue_saturation(Image& img, float hue_deg = 0.f, float sat = 1.0f);

// 18 缩放与裁剪
void stage18_scale_crop(Image& img, float scale = 0.5f, bool crop16x9 = false);

// 19 输出 PNG + 可选 YUV420
void stage19_encoder(const Image& img, const std::string& path,
                     bool write_yuv420 = false);

}  // namespace isp
