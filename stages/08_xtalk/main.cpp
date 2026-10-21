#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_08_xtalk <in.isp> <out.isp> [--strength 0.04]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage08_xtalk(img, a.getf("strength", 0.04f));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "08");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
