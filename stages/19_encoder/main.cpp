#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(
            argc, argv,
            "用法: isp_19_encoder <in.isp> <out.png> [--yuv]");
        isp::Image img = isp::load_isp(a.in);
        isp::stage19_encoder(img, a.out, a.has("yuv"));
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
