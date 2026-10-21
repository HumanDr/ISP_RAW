// 06 Demosaic：Malvar-He-Cutler / 双线性。
#include <algorithm>
#include <cstdio>
#include <stdexcept>
#include <utility>
#include <vector>

#include "isp/stages.h"

namespace isp {
namespace {
float at(const float* p, int w, int h, int x, int y) {
    x = std::min(w - 1, std::max(0, x));
    y = std::min(h - 1, std::max(0, y));
    return p[static_cast<size_t>(y) * w + x];
}
float conv5(const float* p, int w, int h, int x, int y, const float* k) {
    float s = 0;
    for (int dy = -2; dy <= 2; ++dy)
        for (int dx = -2; dx <= 2; ++dx)
            s += at(p, w, h, x + dx, y + dy) * k[(dy + 2) * 5 + (dx + 2)];
    return s;
}
void bilinear(const float* p, int w, int h, const Image& im, int x, int y, float* o) {
    const float c = at(p, w, h, x, y);
    const float l = at(p, w, h, x - 1, y), r = at(p, w, h, x + 1, y);
    const float u = at(p, w, h, x, y - 1), d = at(p, w, h, x, y + 1);
    const float tl = at(p, w, h, x - 1, y - 1), tr = at(p, w, h, x + 1, y - 1);
    const float bl = at(p, w, h, x - 1, y + 1), br = at(p, w, h, x + 1, y + 1);
    const int site = im.cfa_color(x, y);
    if (site == 0) {
        o[0] = c; o[1] = 0.25f * (l + r + u + d); o[2] = 0.25f * (tl + tr + bl + br);
    } else if (site == 2) {
        o[2] = c; o[1] = 0.25f * (l + r + u + d); o[0] = 0.25f * (tl + tr + bl + br);
    } else {
        o[1] = c;
        const int hx = (x == 0) ? x + 1 : x - 1;
        if (im.cfa_color(hx, y) == 0) { o[0] = 0.5f * (l + r); o[2] = 0.5f * (u + d); }
        else { o[0] = 0.5f * (u + d); o[2] = 0.5f * (l + r); }
    }
}
const float kG[25] = {0,0,-1,0,0, 0,0,2,0,0, -1,2,4,2,-1, 0,0,2,0,0, 0,0,-1,0,0};
const float kRgH[25] = {0,0,0.5f,0,0, 0,-1,0,-1,0, -1,4,5,4,-1, 0,-1,0,-1,0, 0,0,0.5f,0,0};
const float kRgV[25] = {0,0,-1,0,0, 0,-1,4,-1,0, 0.5f,0,5,0,0.5f, 0,-1,4,-1,0, 0,0,-1,0,0};
const float kRb[25] = {0,0,-1.5f,0,0, 0,2,0,2,0, -1.5f,0,6,0,-1.5f, 0,2,0,2,0, 0,0,-1.5f,0,0};
}  // namespace

void stage06_demosaic(Image& img, Demosaic method) {
    if (!img.is_bayer()) throw std::runtime_error("Demosaic 需要 Bayer 输入");
    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    const std::vector<float> src(img.pix_f32(), img.pix_f32() + img.pixel_count());
    const float* p = src.data();
    Image out = img;
    out.allocate(DT_F32, w, h, 3);
    out.cfa = CFA_NONE;
    out.space = SPACE_RGB;
    out.black[0] = out.black[1] = out.black[2] = out.black[3] = 0.f;
    out.white = 1.f;
    out.note = method == Demosaic::MHC ? "Demosaic: MHC" : "Demosaic: bilinear";
    float* q = out.pix_f32();
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            float rgb[3];
            const bool border = (x < 2 || y < 2 || x >= w - 2 || y >= h - 2);
            if (method == Demosaic::Bilinear || border) {
                bilinear(p, w, h, img, x, y, rgb);
            } else {
                const int site = img.cfa_color(x, y);
                const float raw = p[static_cast<size_t>(y) * w + x];
                for (int c = 0; c < 3; ++c) {
                    if (c == site) rgb[c] = raw;
                    else if (c == 1) rgb[c] = conv5(p, w, h, x, y, kG) / 8.f;
                    else if (c == 0) {
                        if (site == 1) rgb[c] = conv5(p, w, h, x, y,
                            img.cfa_color(x - 1, y) == 0 ? kRgH : kRgV) / 8.f;
                        else rgb[c] = conv5(p, w, h, x, y, kRb) / 8.f;
                    } else {
                        if (site == 1) rgb[c] = conv5(p, w, h, x, y,
                            img.cfa_color(x - 1, y) == 2 ? kRgH : kRgV) / 8.f;
                        else rgb[c] = conv5(p, w, h, x, y, kRb) / 8.f;
                    }
                }
            }
            for (int c = 0; c < 3; ++c)
                q[(static_cast<size_t>(y) * w + x) * 3 + c] = std::max(0.f, rgb[c]);
        }
    }
    img = std::move(out);
    std::printf("[06 Demosaic] %s -> 3 channels\n",
                method == Demosaic::MHC ? "MHC" : "bilinear");
}

}  // namespace isp
