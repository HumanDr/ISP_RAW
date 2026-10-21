#include <cstdio>
#include <exception>

#include "isp/cli.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(argc, argv, "用法: isp_info <file.isp>");
        isp::IspFileHeader h = isp::read_isp_header(a.in);
        std::printf("file  : %s\n", a.in.c_str());
        std::printf("size  : %u x %u x %u (%s, %u bit)\n", h.width, h.height,
                    h.channels, isp::dtype_name((isp::DType)h.dtype), h.bit_depth);
        std::printf("cfa   : %s   space: %s\n", isp::cfa_name((isp::Cfa)h.cfa),
                    h.space == isp::SPACE_YUV ? "YUV" : "RGB");
        std::printf("black : %.1f %.1f %.1f %.1f  white %.1f\n", h.black[0],
                    h.black[1], h.black[2], h.black[3], h.white);
        std::printf("wb    : %.3f %.3f %.3f\n", h.wb[0], h.wb[1], h.wb[2]);
        std::printf("note  : %s\n", h.note);
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
}
