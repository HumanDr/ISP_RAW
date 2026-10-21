// 10 HDR/WDR：只压缩 >1 的高光，0..1 不动，避免整体变灰。
#include <algorithm>
#include <cstdio>
#include <stdexcept>

#include "isp/stages.h"

namespace isp {

void stage10_hdr_wdr(Image& img, float strength) {
    if (img.channels != 3 || img.space != SPACE_RGB)
        throw std::runtime_error("HDR/WDR 需要 RGB 输入");
    const size_t n = img.pixel_count() * 3;
    float* p = img.pix_f32();
    float maxv = 0;
    for (size_t i = 0; i < n; ++i) maxv = std::max(maxv, p[i]);
    for (size_t i = 0; i < n; ++i) {
        float v = p[i];
        if (v > 1.f) v = 1.f + (v - 1.f) / (1.f + strength * (v - 1.f));
        p[i] = v;
    }
    img.note = "HDR/WDR: highlight soft clip";
    std::printf("[10 HDR/WDR] strength %.2f  max before %.2f -> after %.2f\n",
                strength, maxv, 1.f + (maxv > 1 ? (maxv - 1) / (1 + strength * (maxv - 1)) : 0));
}

}  // namespace isp
