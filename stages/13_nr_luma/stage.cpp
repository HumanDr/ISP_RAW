// 13 NR Luma：只对 Y 做 3x3 双边滤波，U/V 不动。
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <vector>

#include "isp/stages.h"

namespace isp {

void stage13_nr_luma(Image& img, float sigma_range) {
    if (img.channels != 3 || img.space != SPACE_YUV)
        throw std::runtime_error("NR Luma 需要 YUV 输入");
    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    std::vector<float> src(img.pixel_count());
    float* p = img.pix_f32();
    for (size_t i = 0; i < src.size(); ++i) src[i] = p[i * 3];
    float lut[512];
    for (int i = 0; i < 512; ++i) {
        float d = i / 512.f;
        lut[i] = std::exp(-(d * d) / (2.f * sigma_range * sigma_range));
    }
    const float sw[3][3] = {{0.7f, 1.f, 0.7f}, {1.f, 1.6f, 1.f}, {0.7f, 1.f, 0.7f}};
    for (int y = 1; y < h - 1; ++y) {
        for (int x = 1; x < w - 1; ++x) {
            const size_t i = static_cast<size_t>(y) * w + x;
            const float c = src[i];
            float sum = c * sw[1][1], ws = sw[1][1];
            for (int dy = -1; dy <= 1; ++dy)
                for (int dx = -1; dx <= 1; ++dx) {
                    if (!dx && !dy) continue;
                    const float v = src[i + dy * w + dx];
                    const int li = std::min(511, static_cast<int>(std::fabs(v - c) * 1024.f));
                    const float wgt = sw[dy + 1][dx + 1] * lut[li];
                    sum += v * wgt; ws += wgt;
                }
            p[i * 3] = sum / ws;
        }
    }
    img.note = "NR Luma: bilateral on Y";
    std::printf("[13 NR Luma] sigma %.4f\n", sigma_range);
}

}  // namespace isp
