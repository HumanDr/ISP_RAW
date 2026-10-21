#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_15_contrast_brightness <in.isp> <out.isp> [--contrast 1.02] [--brightness 0]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage15_contrast_brightness(img, a.getf("contrast", 1.02f), a.getf("brightness", 0.f));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "15");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
