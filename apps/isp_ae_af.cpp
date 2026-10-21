// AE/AF 是控制闭环，不是图像链路节点。
// 这个工具从 RAW 直接统计：AE 用亮度分位数，AF 用绿色通道梯度。
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <exception>
#include <vector>

#include "isp/cli.h"
#include "isp/raw.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(
            argc, argv,
            "用法: isp_ae_af <input.raw> [--meta sample.meta]");
        isp::Image img = isp::load_raw(a.in, a.get("meta", ""));
        const float* p = img.pix_f32();
        if (img.dtype == isp::DT_U16) {
            img.require_f32();
            p = img.pix_f32();
        }
        std::vector<float> lum;
        lum.reserve(img.pixel_count() / 8 + 1);
        double sum = 0;
        const int w = img.width, h = img.height;
        auto norm = [&](float v, int x, int y) {
            const int pos = img.cfa_pos(x, y);
            return (v - img.black[pos]) / std::max(1.f, img.white - img.black[pos]);
        };
        for (int y = 0; y < h; y += 2)
            for (int x = 0; x < w; x += 2) {
                const float v = norm(p[static_cast<size_t>(y) * w + x], x, y);
                lum.push_back(v);
                sum += v;
            }
        std::sort(lum.begin(), lum.end());
        auto q = [&](double t) { return lum[static_cast<size_t>(t * (lum.size() - 1))]; };
        const float p50 = q(0.50), p99 = q(0.99);
        const float mean = static_cast<float>(sum / lum.size());
        const float target = 0.18f * 0.98f;
        const float ev = std::log2(target / std::max(1e-5f, p50));

        double focus = 0;
        size_t cnt = 0;
        for (int y = 0; y < h - 2; y += 2)
            for (int x = 0; x < w - 2; ++x) {
                if (img.cfa_color(x, y) != 1) continue;
                const float g = p[static_cast<size_t>(y) * w + x];
                focus += std::fabs(norm(g, x, y) - norm(p[static_cast<size_t>(y) * w + x + 2], x + 2, y)) +
                         std::fabs(norm(g, x, y) - norm(p[static_cast<size_t>(y + 2) * w + x], x, y + 2));
                ++cnt;
            }
        std::printf("AE  mean %.4f  p50 %.4f  p99 %.4f  ->  suggest %+.2f EV\n",
                    mean, p50, p99, ev);
        std::printf("AF  green gradient/frame %.5f (越大越接近合焦)\n",
                    cnt ? focus / cnt : 0.0);
        std::printf("注意：这是统计值；真正的 AE/AF 还要驱动曝光/马达，再重新采集。\n");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
