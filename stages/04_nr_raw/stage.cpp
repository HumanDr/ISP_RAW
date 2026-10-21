// 04 NR RAW：RAW 域双边滤波，只对同色邻居采样。
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <vector>

#include "isp/stages.h"

namespace isp {
namespace {
float estimate_noise(const float* p, int w, int h) {
    std::vector<float> d;
    d.reserve(static_cast<size_t>(w) * h / 16);
    for (int y = 2; y < h - 2; y += 3)
        for (int x = 2; x < w - 4; x += 3)
            d.push_back(std::fabs(p[static_cast<size_t>(y) * w + x] -
                                  p[static_cast<size_t>(y) * w + x + 2]));
    if (d.empty()) return 0.01f;
    size_t k = d.size() / 2;
    std::nth_element(d.begin(), d.begin() + k, d.end());
    return std::max(0.001f, d[k] / 0.9539f);
}
}  // namespace

void stage04_nr_raw(Image& img, float sigma_range) {
    if (!img.is_bayer() || img.dtype != DT_F32)
        throw std::runtime_error("NR RAW 需要 f32 Bayer 输入");
    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    const float* s = img.pix_f32();
    const float noise = estimate_noise(s, w, h);
    if (sigma_range <= 0.f) sigma_range = std::max(0.006f, 1.5f * noise);

    static const int dx[12] = {-2, 2, 0, 0, -1, 1, -1, 1, -2, 2, -2, 2};
    static const int dy[12] = {0, 0, -2, 2, -1, -1, 1, 1, -2, -2, 2, 2};
    float sw[12];
    for (int k = 0; k < 12; ++k)
        sw[k] = std::exp(-(dx[k] * dx[k] + dy[k] * dy[k]) / (2.f * 1.2f * 1.2f));
    float lut[1024];
    for (int i = 0; i < 1024; ++i) {
        float d = i / 1024.f;
        lut[i] = std::exp(-(d * d) / (2.f * sigma_range * sigma_range));
    }

    std::vector<float> copy(s, s + img.pixel_count());
    const float* src = copy.data();
    float* dst = img.pix_f32();
    for (int y = 2; y < h - 2; ++y) {
        for (int x = 2; x < w - 2; ++x) {
            const size_t i = static_cast<size_t>(y) * w + x;
            const float c = src[i];
            float sum = c, ws = 1.f;
            for (int k = 0; k < 12; ++k) {
                const float v = src[i + dy[k] * w + dx[k]];
                const int li = std::min(1023, static_cast<int>(std::fabs(v - c) * 1024.f));
                const float wgt = sw[k] * lut[li];
                sum += v * wgt; ws += wgt;
            }
            dst[i] = sum / ws;
        }
    }
    img.note = "NR RAW: bilateral";
    std::printf("[04 NR RAW] noise sigma≈%.4f  range sigma=%.4f\n", noise, sigma_range);
}

}  // namespace isp
