#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_13_nr_luma <in.isp> <out.isp> [--sigma 0.012]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage13_nr_luma(img, a.getf("sigma", 0.012f));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "13");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
