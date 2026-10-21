// 14 Edge Enhance：只对 Y 做 unsharp mask。
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <vector>

#include "isp/stages.h"

namespace isp {

void stage14_edge_enhance(Image& img, float amount) {
    if (img.channels != 3 || img.space != SPACE_YUV)
        throw std::runtime_error("Edge Enhance 需要 YUV 输入");
    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    const size_t n = img.pixel_count();
    std::vector<float> y(n), blur(n);
    float* p = img.pix_f32();
    for (size_t i = 0; i < n; ++i) y[i] = p[i * 3];
    const float k[3] = {0.25f, 0.5f, 0.25f};
    for (int r = 0; r < h; ++r)
        for (int c = 0; c < w; ++c) {
            float s = 0;
            for (int t = -1; t <= 1; ++t) {
                int cc = std::min(w - 1, std::max(0, c + t));
                s += y[static_cast<size_t>(r) * w + cc] * k[t + 1];
            }
            blur[static_cast<size_t>(r) * w + c] = s;
        }
    std::vector<float> tmp = blur;
    for (int r = 0; r < h; ++r)
        for (int c = 0; c < w; ++c) {
            float s = 0;
            for (int t = -1; t <= 1; ++t) {
                int rr = std::min(h - 1, std::max(0, r + t));
                s += tmp[static_cast<size_t>(rr) * w + c] * k[t + 1];
            }
            const size_t i = static_cast<size_t>(r) * w + c;
            const float detail = y[i] - s;
            if (std::fabs(detail) > 0.004f)
                p[i * 3] = std::min(1.f, std::max(0.f, y[i] + amount * detail));
        }
    img.note = "Edge Enhance: unsharp on Y";
    std::printf("[14 Edge Enhance] amount %.2f\n", amount);
}

}  // namespace isp
