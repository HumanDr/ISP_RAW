// 15 Contrast/Brightness：只改 Y。
#include <algorithm>
#include <cstdio>
#include <stdexcept>

#include "isp/stages.h"

namespace isp {

void stage15_contrast_brightness(Image& img, float contrast, float brightness) {
    if (img.channels != 3 || img.space != SPACE_YUV)
        throw std::runtime_error("Contrast/Brightness 需要 YUV 输入");
    float* p = img.pix_f32();
    const size_t n = img.pixel_count();
    for (size_t i = 0; i < n; ++i) {
        float y = (p[i * 3] - 0.5f) * contrast + 0.5f + brightness;
        p[i * 3] = std::min(1.f, std::max(0.f, y));
    }
    img.note = "Contrast/Brightness on Y";
    std::printf("[15 Contrast/Brightness] contrast %.2f brightness %+.2f\n",
                contrast, brightness);
}

}  // namespace isp
