// 07 NR Color：在 YUV 域只对 Cb/Cr 做 3x3 中值，亮度保持。
#include <algorithm>
#include <cstdio>
#include <stdexcept>
#include <vector>

#include "isp/stages.h"

namespace isp {

void stage07_nr_color(Image& img, float strength) {
    if (img.channels != 3 || img.space != SPACE_RGB)
        throw std::runtime_error("NR Color 需要 RGB 输入");
    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    const size_t n = img.pixel_count();
    std::vector<float> Y(n), U(n), V(n);
    const float* p = img.pix_f32();
    for (size_t i = 0; i < n; ++i) {
        const float r = p[i * 3], g = p[i * 3 + 1], b = p[i * 3 + 2];
        Y[i] = 0.2126f * r + 0.7152f * g + 0.0722f * b;
        U[i] = (b - Y[i]) / 1.8556f;
        V[i] = (r - Y[i]) / 1.5748f;
    }
    auto med3 = [&](const std::vector<float>& a, int x, int y) {
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
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const size_t i = static_cast<size_t>(y) * w + x;
            const float u = med3(U, x, y), v = med3(V, x, y);
            U[i] = U[i] * (1 - strength) + u * strength;
            V[i] = V[i] * (1 - strength) + v * strength;
            const float r = Y[i] + 1.5748f * V[i];
            const float g = Y[i] - 0.1873f * U[i] - 0.4681f * V[i];
            const float b = Y[i] + 1.8556f * U[i];
            img.pix_f32()[i * 3] = std::max(0.f, r);
            img.pix_f32()[i * 3 + 1] = std::max(0.f, g);
            img.pix_f32()[i * 3 + 2] = std::max(0.f, b);
        }
    }
    img.note = "NR Color: chroma median";
    std::printf("[07 NR Color] chroma median strength %.2f\n", strength);
}

}  // namespace isp
