// 08 X-talking：颜色串扰校正。滤光片不是理想窄带，R/G/B 会互相漏。
#include <algorithm>
#include <cstdio>
#include <stdexcept>

#include "isp/stages.h"

namespace isp {

void stage08_xtalk(Image& img, float strength) {
    if (img.channels != 3 || img.space != SPACE_RGB)
        throw std::runtime_error("X-talking 需要 RGB 输入");
    // 对角 1，非对角 -strength；再按行归一化，保证白点不变。
    float m[9];
    for (int r = 0; r < 3; ++r)
        for (int c = 0; c < 3; ++c)
            m[r * 3 + c] = (r == c) ? 1.f : -strength;
    for (int r = 0; r < 3; ++r) {
        float s = m[r * 3] + m[r * 3 + 1] + m[r * 3 + 2];
        for (int c = 0; c < 3; ++c) m[r * 3 + c] /= s;
    }
    const size_t n = img.pixel_count();
    float* p = img.pix_f32();
    for (size_t i = 0; i < n; ++i) {
        const float r = p[i * 3], g = p[i * 3 + 1], b = p[i * 3 + 2];
        p[i * 3] = std::max(0.f, m[0] * r + m[1] * g + m[2] * b);
        p[i * 3 + 1] = std::max(0.f, m[3] * r + m[4] * g + m[5] * b);
        p[i * 3 + 2] = std::max(0.f, m[6] * r + m[7] * g + m[8] * b);
    }
    img.note = "X-talking: color crosstalk correction";
    std::printf("[08 X-talking] strength %.2f\n", strength);
}

}  // namespace isp
