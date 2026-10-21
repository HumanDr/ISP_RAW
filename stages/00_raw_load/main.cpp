#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/raw.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(
            argc, argv,
            "用法: isp_00_raw_load <input.raw> <output.isp> [--meta sample.meta]");
        isp::Image img;
        isp::stage00_raw_load(a.in, img, a.get("meta", ""));
        isp::save_isp(a.out, img);
        isp::print_stats(img, "00");
        std::printf("        camera: %s\n", img.camera.c_str());
        std::printf("        CFA %s  black %.0f/%.0f/%.0f/%.0f  white %.0f\n",
                    isp::cfa_name(img.cfa), img.black[0], img.black[1],
                    img.black[2], img.black[3], img.white);
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
