// =============================================================================
//  io.h  --  把内存里的 8bit RGB 写成 PNG / PPM
//  只依赖 libpng（系统自带），不引入 OpenCV，保证新手能看懂每一行。
// =============================================================================
#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace isp {

void write_png_rgb8(const std::string& path, int w, int h,
                    const uint8_t* rgb);
void write_png_gray8(const std::string& path, int w, int h,
                     const uint8_t* gray);
void write_ppm_rgb8(const std::string& path, int w, int h, const uint8_t* rgb);

}  // namespace isp
