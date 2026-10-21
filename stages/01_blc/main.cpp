#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_01_blc <in.isp> <out.isp> [--noclip]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage01_blc(img, !a.has("noclip"));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "01");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
