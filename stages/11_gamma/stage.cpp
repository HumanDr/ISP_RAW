// 11 Gamma：自动曝光 + sRGB 传输函数。
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <stdexcept>
#include <vector>

#include "isp/color.h"
#include "isp/stages.h"

namespace isp {

void stage11_gamma(Image& img, bool auto_exposure, float ev) {
    if (img.channels != 3 || img.space != SPACE_RGB)
        throw std::runtime_error("Gamma 需要 RGB 输入");
    const size_t n = img.pixel_count();
    float* p = img.pix_f32();
    float scale = std::pow(2.f, ev);
    if (auto_exposure) {
        std::vector<float> hi;
        const size_t step = std::max<size_t>(1, n / 200000);
        hi.reserve(n / step + 1);
        for (size_t i = 0; i < n; i += step)
            hi.push_back(std::max({p[i * 3], p[i * 3 + 1], p[i * 3 + 2]}));
        size_t k = static_cast<size_t>(0.995 * (hi.size() - 1));
        std::nth_element(hi.begin(), hi.begin() + k, hi.end());
        const float p995 = hi[k];
        scale = p995 > 1e-5f ? 0.98f / p995 : 1.f;
        std::printf("[11 Gamma] auto exposure p99.5=%.4f scale=%.3f (%.2f EV)\n",
                    p995, scale, std::log2(scale));
    } else {
        std::printf("[11 Gamma] manual exposure %+.2f EV\n", ev);
    }
    for (size_t i = 0; i < n; ++i)
        for (int c = 0; c < 3; ++c)
            p[i * 3 + c] = clamp01(srgb_encode(p[i * 3 + c] * scale));
    img.exposure = scale;
    img.note = "Gamma: exposure + sRGB transfer";
}

}  // namespace isp
