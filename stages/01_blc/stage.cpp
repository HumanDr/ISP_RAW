// 01 BLC：黑电平校正。传感器“没光”时不是 0，而是一个偏置。
#include <algorithm>
#include <cstdio>
#include <stdexcept>

#include "isp/stages.h"

namespace isp {

void stage01_blc(Image& img, bool clip) {
    if (!img.is_bayer() || img.dtype != DT_U16)
        throw std::runtime_error("BLC 需要 u16 Bayer 输入");
    const float bl[4] = {img.black[0], img.black[1], img.black[2], img.black[3]};
    const float white = img.white;
    img.require_f32();
    float* p = img.pix_f32();
    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const size_t i = static_cast<size_t>(y) * w + x;
            const int pos = img.cfa_pos(x, y);
            const float b = bl[pos];
            float v = (p[i] - b) / std::max(1.f, white - b);
            if (clip) v = std::min(1.f, std::max(0.f, v));
            p[i] = v;
        }
    }
    img.black[0] = img.black[1] = img.black[2] = img.black[3] = 0.f;
    img.white = 1.f;
    img.bit_depth = 32;
    img.note = "BLC: black removed, normalized to [0,1]";
    std::printf("[01 BLC] black %.0f/%.0f/%.0f/%.0f white %.0f -> [0,1]\n",
                bl[0], bl[1], bl[2], bl[3], white);
}

}  // namespace isp
