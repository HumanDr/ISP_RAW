#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_10_hdr_wdr <in.isp> <out.isp> [--strength 0.5]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage10_hdr_wdr(img, a.getf("strength", 0.5f));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "10");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
