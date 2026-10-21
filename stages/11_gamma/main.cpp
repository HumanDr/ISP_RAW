#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_11_gamma <in.isp> <out.isp> [--manual --ev 0]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage11_gamma(img, !a.has("manual"), a.getf("ev", 0.f));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "11");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
