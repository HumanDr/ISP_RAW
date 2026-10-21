// 19 Encoder：YUV -> RGB 写 PNG；可选写 YUV420 planar。
#include <algorithm>
#include <cstdio>
#include <stdexcept>
#include <vector>

#include "isp/io.h"
#include "isp/stages.h"

namespace isp {

void stage19_encoder(const Image& img, const std::string& path, bool write_yuv420) {
    if (img.channels != 3 || img.space != SPACE_YUV)
        throw std::runtime_error("Encoder 需要 YUV 输入");
    const int w = static_cast<int>(img.width), h = static_cast<int>(img.height);
    const float* p = img.pix_f32();
    std::vector<uint8_t> rgb(static_cast<size_t>(w) * h * 3);
    for (size_t i = 0; i < img.pixel_count(); ++i) {
        const float y = p[i * 3], u = p[i * 3 + 1], v = p[i * 3 + 2];
        const float r = y + 1.5748f * v;
        const float g = y - 0.1873f * u - 0.4681f * v;
        const float b = y + 1.8556f * u;
        rgb[i * 3] = static_cast<uint8_t>(std::min(1.f, std::max(0.f, r)) * 255.f + 0.5f);
        rgb[i * 3 + 1] = static_cast<uint8_t>(std::min(1.f, std::max(0.f, g)) * 255.f + 0.5f);
        rgb[i * 3 + 2] = static_cast<uint8_t>(std::min(1.f, std::max(0.f, b)) * 255.f + 0.5f);
    }
    write_png_rgb8(path, w, h, rgb.data());
    std::printf("[19 Encoder] wrote %s (%dx%d)\n", path.c_str(), w, h);

    if (write_yuv420) {
        std::string yp = path;
        const size_t dot = yp.find_last_of('.');
        if (dot != std::string::npos) yp = yp.substr(0, dot);
        yp += ".yuv";
        FILE* fp = std::fopen(yp.c_str(), "wb");
        if (!fp) throw std::runtime_error("无法写 YUV: " + yp);
        std::vector<uint8_t> Y(static_cast<size_t>(w) * h);
        std::vector<uint8_t> U(static_cast<size_t>(w / 2) * (h / 2));
        std::vector<uint8_t> V(static_cast<size_t>(w / 2) * (h / 2));
        for (int y = 0; y < h; ++y)
            for (int x = 0; x < w; ++x) {
                const size_t i = static_cast<size_t>(y) * w + x;
                Y[i] = static_cast<uint8_t>(std::min(1.f, std::max(0.f, p[i * 3])) * 255.f + 0.5f);
            }
        for (int y = 0; y < h / 2; ++y)
            for (int x = 0; x < w / 2; ++x) {
                float su = 0, sv = 0;
                for (int dy = 0; dy < 2; ++dy)
                    for (int dx = 0; dx < 2; ++dx) {
                        const size_t i = (static_cast<size_t>(y * 2 + dy) * w + x * 2 + dx) * 3;
                        su += p[i + 1]; sv += p[i + 2];
                    }
                const size_t j = static_cast<size_t>(y) * (w / 2) + x;
                U[j] = static_cast<uint8_t>((su / 4.f + 0.5f) * 255.f + 0.5f);
                V[j] = static_cast<uint8_t>((sv / 4.f + 0.5f) * 255.f + 0.5f);
            }
        std::fwrite(Y.data(), 1, Y.size(), fp);
        std::fwrite(U.data(), 1, U.size(), fp);
        std::fwrite(V.data(), 1, V.size(), fp);
        std::fclose(fp);
        std::printf("[19 Encoder] wrote %s (YUV420 planar)\n", yp.c_str());
    }
}

}  // namespace isp
