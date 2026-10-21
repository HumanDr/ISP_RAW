// 17 Hue/Saturation：在 YUV 里旋转色度、缩放饱和度。
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <stdexcept>

#include "isp/stages.h"

namespace isp {

void stage17_hue_saturation(Image& img, float hue_deg, float sat) {
    if (img.channels != 3 || img.space != SPACE_YUV)
        throw std::runtime_error("Hue/Saturation 需要 YUV 输入");
    const float a = hue_deg * 3.14159265f / 180.f;
    const float cs = std::cos(a), sn = std::sin(a);
    float* p = img.pix_f32();
    for (size_t i = 0; i < img.pixel_count(); ++i) {
        const float u = p[i * 3 + 1], v = p[i * 3 + 2];
        const float u2 = (u * cs - v * sn) * sat;
        const float v2 = (u * sn + v * cs) * sat;
        p[i * 3 + 1] = std::min(0.5f, std::max(-0.5f, u2));
        p[i * 3 + 2] = std::min(0.5f, std::max(-0.5f, v2));
    }
    img.note = "Hue/Saturation";
    std::printf("[17 Hue/Saturation] hue %+.1f deg  saturation %.2f\n", hue_deg, sat);
}

}  // namespace isp
