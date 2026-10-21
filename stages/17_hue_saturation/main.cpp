#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "isp_17_hue_saturation <in.isp> <out.isp> [--hue 0] [--sat 1.02]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage17_hue_saturation(img, a.getf("hue", 0.f), a.getf("sat", 1.02f));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "17");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
