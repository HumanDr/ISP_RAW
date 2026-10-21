#include "isp/io.h"

#include <png.h>

#include <cstdio>
#include <cstring>
#include <stdexcept>

namespace isp {
namespace {

void png_write_common(const std::string& path, int w, int h, int color_type,
                      const uint8_t* data, int stride) {
    FILE* fp = std::fopen(path.c_str(), "wb");
    if (!fp) throw std::runtime_error("无法写入 PNG: " + path);

    png_structp png = png_create_write_struct(PNG_LIBPNG_VER_STRING, nullptr,
                                              nullptr, nullptr);
    if (!png) {
        std::fclose(fp);
        throw std::runtime_error("png_create_write_struct 失败");
    }
    png_infop info = png_create_info_struct(png);
    if (!info) {
        png_destroy_write_struct(&png, nullptr);
        std::fclose(fp);
        throw std::runtime_error("png_create_info_struct 失败");
    }
    if (setjmp(png_jmpbuf(png))) {
        png_destroy_write_struct(&png, &info);
        std::fclose(fp);
        throw std::runtime_error("libpng 写入异常: " + path);
    }

    png_init_io(png, fp);
    png_set_IHDR(png, info, w, h, 8, color_type, PNG_INTERLACE_NONE,
                 PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
    png_set_compression_level(png, 6);
    // 写一个 sRGB chunk，告诉看图软件"这是 sRGB 图像"。
    png_set_sRGB_gAMA_and_cHRM(png, info, PNG_sRGB_INTENT_PERCEPTUAL);
    png_write_info(png, info);

    std::vector<png_bytep> rows(h);
    for (int y = 0; y < h; ++y)
        rows[y] = const_cast<png_bytep>(data + static_cast<size_t>(y) * stride);
    png_write_image(png, rows.data());
    png_write_end(png, nullptr);
    png_destroy_write_struct(&png, &info);
    std::fclose(fp);
}

}  // namespace

void write_png_rgb8(const std::string& path, int w, int h,
                    const uint8_t* rgb) {
    png_write_common(path, w, h, PNG_COLOR_TYPE_RGB, rgb, w * 3);
}

void write_png_gray8(const std::string& path, int w, int h,
                     const uint8_t* gray) {
    png_write_common(path, w, h, PNG_COLOR_TYPE_GRAY, gray, w);
}

void write_ppm_rgb8(const std::string& path, int w, int h,
                    const uint8_t* rgb) {
    FILE* fp = std::fopen(path.c_str(), "wb");
    if (!fp) throw std::runtime_error("无法写入 PPM: " + path);
    std::fprintf(fp, "P6\n%d %d\n255\n", w, h);
    size_t n = static_cast<size_t>(w) * h * 3;
    if (std::fwrite(rgb, 1, n, fp) != n) {
        std::fclose(fp);
        throw std::runtime_error("PPM 写入失败");
    }
    std::fclose(fp);
}

}  // namespace isp
