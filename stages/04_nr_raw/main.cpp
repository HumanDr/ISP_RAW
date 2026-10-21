#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_04_nr_raw <in.isp> <out.isp> [--sigma 0]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage04_nr_raw(img, a.getf("sigma", 0.f));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "04");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
