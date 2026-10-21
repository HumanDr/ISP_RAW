// 03 BPC/DPC：坏点校正。同色 4 邻域中值，检测孤立极值。
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <vector>

#include "isp/stages.h"

namespace isp {

void stage03_dpc(Image& img, float threshold) {
    if (!img.is_bayer() || img.dtype != DT_F32)
        throw std::runtime_error("DPC 需要 f32 Bayer 输入");
    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    const std::vector<float> src(img.pix_f32(), img.pix_f32() + img.pixel_count());
    float* dst = img.pix_f32();
    size_t fixed = 0, tested = 0;
    for (int y = 2; y < h - 2; ++y) {
        for (int x = 2; x < w - 2; ++x) {
            const size_t i = static_cast<size_t>(y) * w + x;
            const float v = src[i];
            float n[4] = {src[i - 2], src[i + 2], src[i - 2 * w], src[i + 2 * w]};
            std::sort(n, n + 4);
            const float med = 0.5f * (n[1] + n[2]);
            ++tested;
            if (((v <= n[0]) || (v >= n[3])) && std::fabs(v - med) > threshold) {
                dst[i] = med;
                ++fixed;
            }
        }
    }
    img.note = "BPC/DPC: median of same-color neighbors";
    std::printf("[03 BPC/DPC] threshold %.3f  fixed %zu / %zu (%.4f%%)\n",
                threshold, fixed, tested, 100.0 * fixed / std::max<size_t>(1, tested));
}

}  // namespace isp
