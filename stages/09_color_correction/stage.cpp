// 09 Color Correction：相机 RGB -> linear sRGB。
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <stdexcept>

#include "isp/color.h"
#include "isp/stages.h"

namespace isp {

void stage09_color_correction(Image& img, bool normalize_rows) {
    if (img.channels != 3 || img.space != SPACE_RGB)
        throw std::runtime_error("Color Correction 需要 RGB 输入");
    float m[9];
    mat3_mul(xyz_to_srgb_matrix(), img.cam_to_xyz, m);
    if (normalize_rows) {
        for (int r = 0; r < 3; ++r) {
            float s = m[r * 3] + m[r * 3 + 1] + m[r * 3 + 2];
            if (std::fabs(s) > 1e-6f)
                for (int c = 0; c < 3; ++c) m[r * 3 + c] /= s;
        }
    }
    std::printf("[09 Color Correction] camera RGB -> linear sRGB:\n");
    for (int r = 0; r < 3; ++r)
        std::printf("      [% 7.4f % 7.4f % 7.4f]\n", m[r * 3], m[r * 3 + 1], m[r * 3 + 2]);
    const size_t n = img.pixel_count();
    float* p = img.pix_f32();
    for (size_t i = 0; i < n; ++i) {
        const float r = p[i * 3], g = p[i * 3 + 1], b = p[i * 3 + 2];
        p[i * 3] = std::max(0.f, m[0] * r + m[1] * g + m[2] * b);
        p[i * 3 + 1] = std::max(0.f, m[3] * r + m[4] * g + m[5] * b);
        p[i * 3 + 2] = std::max(0.f, m[6] * r + m[7] * g + m[8] * b);
    }
    img.note = "Color Correction: CCM -> linear sRGB";
}

}  // namespace isp
