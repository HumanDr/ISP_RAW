#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_18_scale_crop <in.isp> <out.isp> [--scale 0.5] [--crop]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage18_scale_crop(img, a.getf("scale", 0.5f), a.has("crop"));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "18");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
