#include <cstdio>
#include <exception>

#include "isp/cli.h"
#include "isp/io.h"
#include "isp/preview.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(
            argc, argv,
            "用法: isp_dump <in.isp> <out.png> [--gamma 2.2] [--ev 0] [--linear] [--no-auto]");
        isp::Image img = isp::load_isp(a.in);
        isp::PreviewOptions o;
        o.gamma = a.has("linear") ? 1.f : a.getf("gamma", 2.2f);
        o.ev = a.getf("ev", 0.f);
        o.auto_stretch = !a.has("no-auto");
        isp::Preview pv = isp::make_preview(img, o);
        if (pv.channels == 1)
            isp::write_png_gray8(a.out, pv.width, pv.height, pv.data.data());
        else
            isp::write_png_rgb8(a.out, pv.width, pv.height, pv.data.data());
        std::printf("dumped %s -> %s (%dx%d)\n", a.in.c_str(), a.out.c_str(),
                    pv.width, pv.height);
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
}
