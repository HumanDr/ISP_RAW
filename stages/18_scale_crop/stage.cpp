// 18 Scale & Crop：2x2/4x4 box 缩放，可中心裁成 16:9。
#include <algorithm>
#include <cstdio>
#include <stdexcept>

#include "isp/stages.h"

namespace isp {

void stage18_scale_crop(Image& img, float scale, bool crop16x9) {
    if (img.channels != 3 || img.space != SPACE_YUV)
        throw std::runtime_error("Scale & Crop 需要 YUV 输入");
    int f = 1;
    if (scale > 0.74f) f = 1;
    else if (scale > 0.37f) f = 2;
    else f = 4;
    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    const int ow = w / f, oh = h / f;
    Image out = img;
    out.allocate(DT_F32, ow, oh, 3);
    out.space = SPACE_YUV;
    const float* p = img.pix_f32();
    float* q = out.pix_f32();
    for (int y = 0; y < oh; ++y)
        for (int x = 0; x < ow; ++x)
            for (int c = 0; c < 3; ++c) {
                float s = 0;
                for (int dy = 0; dy < f; ++dy)
                    for (int dx = 0; dx < f; ++dx)
                        s += p[((static_cast<size_t>(y) * f + dy) * w + x * f + dx) * 3 + c];
                q[(static_cast<size_t>(y) * ow + x) * 3 + c] = s / (f * f);
            }

    if (crop16x9) {
        const int target_h = std::min(oh, ow * 9 / 16);
        if (target_h < oh) {
            const int y0 = (oh - target_h) / 2;
            Image crop;
            crop.allocate(DT_F32, ow, target_h, 3);
            crop.space = SPACE_YUV;
            crop.camera = out.camera;
            crop.wb[0] = out.wb[0]; crop.wb[1] = out.wb[1]; crop.wb[2] = out.wb[2];
            for (int r = 0; r < target_h; ++r)
                std::copy(q + (static_cast<size_t>(r + y0) * ow) * 3,
                          q + (static_cast<size_t>(r + y0) * ow) * 3 + ow * 3,
                          crop.pix_f32() + static_cast<size_t>(r) * ow * 3);
            crop.note = "Scale & Crop: " + std::to_string(ow) + "x" + std::to_string(target_h);
            img = std::move(crop);
            std::printf("[18 Scale & Crop] scale 1/%d + crop 16:9 -> %dx%d\n", f, ow, target_h);
            return;
        }
    }
    out.note = "Scale & Crop: " + std::to_string(ow) + "x" + std::to_string(oh);
    img = std::move(out);
    std::printf("[18 Scale & Crop] scale 1/%d -> %dx%d\n", f, ow, oh);
}

}  // namespace isp
