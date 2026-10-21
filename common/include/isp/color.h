// =============================================================================
//  color.h  --  颜色科学里最常用的几个小函数（只有教学需要的部分）
// =============================================================================
#pragma once

#include <algorithm>
#include <cmath>

namespace isp {

// sRGB 传输函数（线性光 -> 显示编码）。注意它和"简单 gamma 2.2"略有不同。
inline float srgb_encode(float v) {
    v = std::max(0.f, v);
    return v <= 0.0031308f ? 12.92f * v
                           : 1.055f * std::pow(v, 1.f / 2.4f) - 0.055f;
}

inline float srgb_decode(float v) {
    v = std::max(0.f, v);
    return v <= 0.04045f ? v / 12.92f
                         : std::pow((v + 0.055f) / 1.055f, 2.4f);
}

// Rec.709 亮度权重（sRGB 原色）
inline float luma709(float r, float g, float b) {
    return 0.2126f * r + 0.7152f * g + 0.0722f * b;
}

inline float clamp01(float v) { return std::min(1.f, std::max(0.f, v)); }

// 行优先 3x3 矩阵乘法：out = A * B
inline void mat3_mul(const float* a, const float* b, float* out) {
    for (int r = 0; r < 3; ++r)
        for (int c = 0; c < 3; ++c)
            out[r * 3 + c] = a[r * 3 + 0] * b[0 * 3 + c] +
                             a[r * 3 + 1] * b[1 * 3 + c] +
                             a[r * 3 + 2] * b[2 * 3 + c];
}

// CIE XYZ (D65) -> linear sRGB
inline const float* xyz_to_srgb_matrix() {
    static const float m[9] = {
        3.2404542f, -1.5371385f, -0.4985314f,
        -0.9692660f, 1.8760108f, 0.0415560f,
        0.0556434f, -0.2040259f, 1.0572252f,
    };
    return m;
}


// 3x3 求逆（行优先）。行列式太小时返回 false。
inline bool mat3_inv(const float* m, float* out) {
    const float a = m[0], b = m[1], c = m[2];
    const float d = m[3], e = m[4], f = m[5];
    const float g = m[6], h = m[7], i = m[8];
    const float det = a * (e * i - f * h) - b * (d * i - f * g) +
                      c * (d * h - e * g);
    if (std::fabs(det) < 1e-12f) return false;
    const float inv = 1.f / det;
    out[0] = (e * i - f * h) * inv;
    out[1] = (c * h - b * i) * inv;
    out[2] = (b * f - c * e) * inv;
    out[3] = (f * g - d * i) * inv;
    out[4] = (a * i - c * g) * inv;
    out[5] = (c * d - a * f) * inv;
    out[6] = (d * h - e * g) * inv;
    out[7] = (b * g - a * h) * inv;
    out[8] = (a * e - b * d) * inv;
    return true;
}

// Bradford 色适应：把"源白点"下的 XYZ 变换到"目标白点"下。
// 相机在暖光下拍的白纸，经过它才会在 D65 显示器上仍然是白的。
inline void bradford_adapt(const float src_white[3], const float dst_white[3],
                           float out[9]) {
    static const float MA[9] = {
        0.8951f, 0.2664f, -0.1614f,
        -0.7502f, 1.7135f, 0.0367f,
        0.0389f, -0.0685f, 1.0296f};
    float mai[9];
    mat3_inv(MA, mai);
    float cs[3], cd[3];
    for (int r = 0; r < 3; ++r) {
        cs[r] = MA[r * 3] * src_white[0] + MA[r * 3 + 1] * src_white[1] +
                MA[r * 3 + 2] * src_white[2];
        cd[r] = MA[r * 3] * dst_white[0] + MA[r * 3 + 1] * dst_white[1] +
                MA[r * 3 + 2] * dst_white[2];
    }
    float D[9] = {0};
    for (int r = 0; r < 3; ++r) D[r * 3 + r] = cd[r] / std::max(1e-9f, cs[r]);
    float t[9];
    mat3_mul(D, MA, t);
    mat3_mul(mai, t, out);
}

inline const float* d65_white() {
    static const float w[3] = {0.95047f, 1.f, 1.08883f};
    return w;
}
inline const float* d50_white() {
    static const float w[3] = {0.96422f, 1.f, 0.82521f};
    return w;
}
inline const float* a_white() {  // Standard Light A (2856K)
    static const float w[3] = {1.09850f, 1.f, 0.35585f};
    return w;
}

}  // namespace isp
