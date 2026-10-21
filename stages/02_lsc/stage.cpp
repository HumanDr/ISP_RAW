// 02 LSC：用径向中位数估计暗角，再用增益把四角提亮。真实产品用 flat-field。
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <vector>

#include "isp/stages.h"

namespace isp {

void stage02_lsc(Image& img, float strength) {
    if (!img.is_bayer() || img.dtype != DT_F32)
        throw std::runtime_error("LSC 需要 f32 Bayer 输入");
    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    const int RB = 64, VB = 512;
    std::vector<uint32_t> hist(static_cast<size_t>(3) * RB * VB, 0);
    const float cx = (w - 1) * 0.5f, cy = (h - 1) * 0.5f;
    const float rmax = std::sqrt(cx * cx + cy * cy);
    const float* p = img.pix_f32();

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const float dx = x - cx, dy = y - cy;
            const float r = std::sqrt(dx * dx + dy * dy) / rmax;
            const int rb = std::min(RB - 1, static_cast<int>(r * RB));
            const int c = img.cfa_color(x, y);
            const int vb = std::min(VB - 1, static_cast<int>(
                std::min(1.f, std::max(0.f, p[static_cast<size_t>(y) * w + x])) * VB));
            ++hist[(static_cast<size_t>(c) * RB + rb) * VB + vb];
        }
    }

    std::vector<float> prof(static_cast<size_t>(3) * RB, 1.f);
    for (int c = 0; c < 3; ++c) {
        for (int b = 0; b < RB; ++b) {
            const uint32_t* hb = &hist[(static_cast<size_t>(c) * RB + b) * VB];
            uint64_t total = 0;
            for (int v = 0; v < VB; ++v) total += hb[v];
            if (total < 200) { prof[c * RB + b] = -1.f; continue; }
            uint64_t acc = 0;
            for (int v = 0; v < VB; ++v) {
                acc += hb[v];
                if (acc * 2 >= total) {
                    prof[c * RB + b] = (v + 0.5f) / VB;
                    break;
                }
            }
        }
        float last = 1.f;
        for (int b = 0; b < RB; ++b) {
            if (prof[c * RB + b] > 0) last = prof[c * RB + b];
            else prof[c * RB + b] = last;
        }
        // 5 点平滑
        std::vector<float> tmp(prof.begin() + c * RB, prof.begin() + (c + 1) * RB);
        for (int b = 0; b < RB; ++b) {
            float s = 0, ws = 0;
            for (int k = -2; k <= 2; ++k) {
                int bb = std::min(RB - 1, std::max(0, b + k));
                float wgt = 3.f - std::abs(k);
                s += tmp[bb] * wgt; ws += wgt;
            }
            prof[c * RB + b] = s / ws;
        }
    }

    std::vector<float> gain(static_cast<size_t>(3) * RB, 1.f);
    for (int c = 0; c < 3; ++c) {
        float ref = 0;
        for (int b = 0; b < 4; ++b) ref += prof[c * RB + b];
        ref *= 0.25f;
        for (int b = 0; b < RB; ++b) {
            float g = std::min(2.5f, std::max(1.f, ref / std::max(1e-5f, prof[c * RB + b])));
            gain[c * RB + b] = 1.f + strength * (g - 1.f);
        }
    }

    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            const float dx = x - cx, dy = y - cy;
            const float rb = std::sqrt(dx * dx + dy * dy) / rmax * RB;
            const int b0 = std::min(RB - 1, static_cast<int>(rb));
            const int b1 = std::min(RB - 1, b0 + 1);
            const float t = rb - b0;
            const int c = img.cfa_color(x, y);
            const float g = gain[c * RB + b0] * (1 - t) + gain[c * RB + b1] * t;
            const size_t i = static_cast<size_t>(y) * w + x;
            img.pix_f32()[i] = p[i] * g;
        }
    }
    img.note = "LSC: radial gain";
    std::printf("[02 LSC] strength %.2f  corner R/G/B = %.2f/%.2f/%.2f\n",
                strength, gain[RB - 1], gain[RB + RB - 1], gain[2 * RB + RB - 1]);
}

}  // namespace isp
