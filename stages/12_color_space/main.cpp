#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_12_color_space <in.isp> <out.isp>");
        isp::Image img = isp::load_isp(a.in);
        isp::stage12_color_space(img);
        isp::save_isp(a.out, img);
        isp::print_stats(img, "12");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
