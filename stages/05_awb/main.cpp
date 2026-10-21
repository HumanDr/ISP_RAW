#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_05_awb <in.isp> <out.isp> [--no-gray-world] [--strength 0.6]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage05_awb(img, !a.has("no-gray-world"), a.getf("strength", 0.6f));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "05");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
