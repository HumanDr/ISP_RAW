// 16 NR Chroma：3x3 中值滤波 U/V，Y 不动。
#include <algorithm>
#include <cstdio>
#include <stdexcept>
#include <vector>

#include "isp/stages.h"

namespace isp {

void stage16_nr_chroma(Image& img, float strength) {
    if (img.channels != 3 || img.space != SPACE_YUV)
        throw std::runtime_error("NR Chroma 需要 YUV 输入");
    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    const size_t n = img.pixel_count();
    std::vector<float> U(n), V(n);
    float* p = img.pix_f32();
    for (size_t i = 0; i < n; ++i) { U[i] = p[i * 3 + 1]; V[i] = p[i * 3 + 2]; }
    auto med = [&](const std::vector<float>& a, int x, int y) {
        float v[9];
        int k = 0;
        for (int dy = -1; dy <= 1; ++dy)
            for (int dx = -1; dx <= 1; ++dx) {
                int xx = std::min(w - 1, std::max(0, x + dx));
                int yy = std::min(h - 1, std::max(0, y + dy));
                v[k++] = a[static_cast<size_t>(yy) * w + xx];
            }
        std::sort(v, v + 9);
        return v[4];
    };
    for (int y = 0; y < h; ++y)
        for (int x = 0; x < w; ++x) {
            const size_t i = static_cast<size_t>(y) * w + x;
            const float u = med(U, x, y), v = med(V, x, y);
            p[i * 3 + 1] = U[i] * (1 - strength) + u * strength;
            p[i * 3 + 2] = V[i] * (1 - strength) + v * strength;
        }
    img.note = "NR Chroma: median on U/V";
    std::printf("[16 NR Chroma] strength %.2f\n", strength);
}

}  // namespace isp
