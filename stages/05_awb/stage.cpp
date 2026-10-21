// 05 AWB：灰度世界 + 与 meta 参考增益混合。
#include <algorithm>
#include <cstdio>
#include <vector>

#include "isp/stages.h"

namespace isp {

void stage05_awb(Image& img, bool gray_world, float strength) {
    float gain[3] = {img.wb[0], img.wb[1], img.wb[2]};
    if (gray_world) {
        double sum[3] = {0, 0, 0};
        size_t cnt[3] = {0, 0, 0};
        const float* p = img.pix_f32();
        const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
        for (int y = 0; y < h; ++y) {
            for (int x = 0; x < w; ++x) {
                const int c = img.cfa_color(x, y);
                const size_t i = static_cast<size_t>(y) * w + x;
                const float v = p[i];
                if (v < 0.95f) { sum[c] += v; ++cnt[c]; }
            }
        }
        double mean[3];
        for (int c = 0; c < 3; ++c) mean[c] = cnt[c] ? sum[c] / cnt[c] : 1.0;
        if (mean[1] > 1e-9) {
            for (int c = 0; c < 3; ++c)
                gain[c] = static_cast<float>(mean[1] / std::max(1e-9, mean[c]));
        }
    }
    // 和相机写入的参考增益混合，避免灰度世界在单色场景里跑偏
    for (int c = 0; c < 3; ++c)
        gain[c] = (1.f - strength) * img.wb[c] + strength * gain[c];
    gain[1] = 1.f;

    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    float* p = img.pix_f32();
    for (int y = 0; y < h; ++y)
        for (int x = 0; x < w; ++x)
            p[static_cast<size_t>(y) * w + x] *= gain[img.cfa_color(x, y)];
    img.wb[0] = gain[0]; img.wb[1] = 1.f; img.wb[2] = gain[2];
    img.note = "AWB: gray world blended with camera reference";
    std::printf("[05 AWB] %s  strength %.2f  gains R/G/B = %.3f/1/%.3f\n",
                gray_world ? "gray-world" : "meta", strength, gain[0], gain[2]);
}

}  // namespace isp
