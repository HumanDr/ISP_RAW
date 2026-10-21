#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_14_edge_enhance <in.isp> <out.isp> [--amount 0.4]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage14_edge_enhance(img, a.getf("amount", 0.4f));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "14");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
