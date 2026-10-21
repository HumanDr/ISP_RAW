#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_03_dpc <in.isp> <out.isp> [--threshold 0.05]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage03_dpc(img, a.getf("threshold", 0.05f));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "03");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
