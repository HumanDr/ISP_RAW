#include "isp/preview.h"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace isp {
namespace {
float percentile(std::vector<float>& v, float pct) {
    if (v.empty()) return 0.f;
    size_t k = static_cast<size_t>(pct / 100.0 * (v.size() - 1));
    std::nth_element(v.begin(), v.begin() + k, v.end());
    return v[k];
}
}  // namespace

Preview make_preview(const Image& img, const PreviewOptions& opt) {
    if (img.data.empty()) throw std::runtime_error("make_preview: 空图像");
    const size_t n = img.sample_count();
    const bool gray = (img.channels == 1);
    const bool yuv = (img.space == SPACE_YUV && img.channels == 3);
    const float inv_gamma = 1.f / std::max(0.01f, opt.gamma);

    auto yuv_to_rgb = [](float y, float u, float v, float* rgb) {
        rgb[0] = y + 1.5748f * v;
        rgb[1] = y - 0.1873f * u - 0.4681f * v;
        rgb[2] = y + 1.8556f * u;
    };

    // 1) 采样（最多 ~30 万个点），求分位数，避免整幅排序。
    std::vector<float> sample;
    const size_t step = std::max<size_t>(1, n / 300000);
    sample.reserve(n / step + 1);
    for (size_t i = 0; i < n; i += step) {
        float v = (img.dtype == DT_U16) ? static_cast<float>(img.pix_u16()[i])
                                        : img.pix_f32()[i];
        if (yuv && i % 3 == 0) {
            float rgb[3];
            yuv_to_rgb(img.pix_f32()[i], img.pix_f32()[i + 1],
                       img.pix_f32()[i + 2], rgb);
            v = std::max({rgb[0], rgb[1], rgb[2]});
        }
        sample.push_back(v);
    }
    float lo = 0.f, hi = 1.f;
    if (img.dtype == DT_U16 && !opt.auto_stretch) {
        lo = 0.f;
        hi = img.white;
    }
    if (opt.auto_stretch) {
        lo = percentile(sample, opt.lo_pct);
        hi = percentile(sample, opt.hi_pct);
        if (!(hi > lo)) { lo = 0.f; hi = 1.f; }
    } else if (img.dtype == DT_F32) {
        lo = 0.f; hi = 1.f;
    }
    const float gain = std::pow(2.f, opt.ev) / (hi - lo);

    Preview out;
    out.width = static_cast<int>(img.width);
    out.height = static_cast<int>(img.height);
    out.channels = gray ? 1 : 3;
    out.data.resize(static_cast<size_t>(img.width) * img.height * out.channels);

    auto encode = [&](float v) -> uint8_t {
        v = (v - lo) * gain;
        v = std::min(1.f, std::max(0.f, v));
        v = std::pow(v, inv_gamma);
        return static_cast<uint8_t>(v * 255.f + 0.5f);
    };

    if (gray) {
        const float* f = (img.dtype == DT_F32) ? img.pix_f32() : nullptr;
        const uint16_t* u = (img.dtype == DT_U16) ? img.pix_u16() : nullptr;
        for (size_t i = 0; i < img.pixel_count(); ++i)
            out.data[i] = encode(f ? f[i] : static_cast<float>(u[i]));
    } else {
        const float* f = (img.dtype == DT_F32) ? img.pix_f32() : nullptr;
        const uint16_t* u = (img.dtype == DT_U16) ? img.pix_u16() : nullptr;
        for (size_t i = 0; i < img.pixel_count(); ++i) {
            if (yuv) {
                float rgb[3];
                yuv_to_rgb(f[i * 3], f[i * 3 + 1], f[i * 3 + 2], rgb);
                for (int c = 0; c < 3; ++c) out.data[i * 3 + c] = encode(rgb[c]);
            } else {
                for (int c = 0; c < 3; ++c) {
                    float v = f ? f[i * 3 + c] : static_cast<float>(u[i * 3 + c]);
                    out.data[i * 3 + c] = encode(v);
                }
            }
        }
    }
    return out;
}

}  // namespace isp
