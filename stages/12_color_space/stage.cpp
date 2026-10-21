// 12 Color Space Convert：RGB -> YUV(BT.709, full range)。
#include <algorithm>
#include <cstdio>
#include <stdexcept>

#include "isp/stages.h"

namespace isp {

void stage12_color_space(Image& img) {
    if (img.channels != 3 || img.space != SPACE_RGB)
        throw std::runtime_error("Color Space Convert 需要 RGB 输入");
    const size_t n = img.pixel_count();
    float* p = img.pix_f32();
    for (size_t i = 0; i < n; ++i) {
        const float r = p[i * 3], g = p[i * 3 + 1], b = p[i * 3 + 2];
        const float y = 0.2126f * r + 0.7152f * g + 0.0722f * b;
        p[i * 3] = std::min(1.f, std::max(0.f, y));
        p[i * 3 + 1] = std::min(0.5f, std::max(-0.5f, (b - y) / 1.8556f));
        p[i * 3 + 2] = std::min(0.5f, std::max(-0.5f, (r - y) / 1.5748f));
    }
    img.space = SPACE_YUV;
    img.note = "Color Space Convert: RGB -> YUV BT.709";
    std::printf("[12 Color Space] RGB -> YUV (BT.709 full range)\n");
}

}  // namespace isp
