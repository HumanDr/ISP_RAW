// =============================================================================
//  isp_pipeline  --  按“RAW 域 -> RGB 域 -> YUV 域”串起 19 个阶段
// =============================================================================
#include <cstdio>
#include <exception>
#include <filesystem>
#include <functional>
#include <string>
#include <vector>

#include "isp/cli.h"
#include "isp/stages.h"

int main(int argc, char** argv) {
    try {
        isp::Args a = isp::parse_args(
            argc, argv,
            "用法: isp_pipeline [--raw data/sample.raw] [--meta data/sample.meta]\n"
            "                   [--out out/final.png] [--work out] [--keep] [--yuv]\n"
            "                   [--lsc 0.7] [--dpc 0.05] [--nrraw 0]\n"
            "                   [--awb-strength 0.6] [--no-gray-world]\n"
            "                   [--method mhc|bilinear] [--xtalk 0.04]\n"
            "                   [--wdr 0.5] [--manual --ev 0]\n"
            "                   [--scale 0.5] [--no-crop]\n"
            "                   [--nr-luma 0.012] [--edge 0.4]\n"
            "                   [--contrast 1.02] [--brightness 0]\n"
            "                   [--nr-chroma 0.5] [--hue 0] [--sat 1.02]",
            false);
        const std::string raw = a.get("raw", "data/sample.raw");
        const std::string meta = a.get("meta", "data/sample.meta");
        const std::string out = a.get("out", "out/final.png");
        const std::string work = a.get("work", "out");
        const bool keep = a.has("keep");
        const bool yuv = a.has("yuv");
        if (keep) std::filesystem::create_directories(work);
        if (std::filesystem::path(out).has_parent_path())
            std::filesystem::create_directories(std::filesystem::path(out).parent_path());

        std::printf("============================================================\n");
        std::printf(" RAW ISP 教学流水线（.raw -> PNG）\n");
        std::printf("   RAW : %s\n   META: %s\n   OUT : %s\n", raw.c_str(), meta.c_str(), out.c_str());
        std::printf("============================================================\n");

        isp::Image img;
        std::vector<std::pair<std::string, double>> times;
        auto run = [&](const std::string& name, const std::function<void()>& fn) {
            std::printf("\n--- %s ---\n", name.c_str());
            isp::Timer t;
            fn();
            times.push_back({name, t.ms()});
            isp::print_stats(img, name.substr(0, 2).c_str());
            if (keep) {
                const std::string p = work + "/" + name + ".isp";
                isp::save_isp(p, img);
                std::printf("        saved %s\n", p.c_str());
            }
        };

        run("00_raw_load", [&] { isp::stage00_raw_load(raw, img, meta); });
        run("01_blc", [&] { isp::stage01_blc(img, true); });
        run("02_lsc", [&] { isp::stage02_lsc(img, a.getf("lsc", 0.7f)); });
        run("03_dpc", [&] { isp::stage03_dpc(img, a.getf("dpc", 0.05f)); });
        run("04_nr_raw", [&] { isp::stage04_nr_raw(img, a.getf("nrraw", 0.f)); });
        run("05_awb", [&] {
            isp::stage05_awb(img, !a.has("no-gray-world"),
                             a.getf("awb-strength", 0.5f));
        });
        run("06_demosaic", [&] {
            isp::stage06_demosaic(img, a.get("method", "mhc") == "bilinear"
                                           ? isp::Demosaic::Bilinear
                                           : isp::Demosaic::MHC);
        });
        run("07_nr_color", [&] { isp::stage07_nr_color(img, a.getf("nr-color", 0.4f)); });
        run("08_xtalk", [&] { isp::stage08_xtalk(img, a.getf("xtalk", 0.04f)); });
        run("09_color_correction", [&] { isp::stage09_color_correction(img, true); });
        run("10_hdr_wdr", [&] { isp::stage10_hdr_wdr(img, a.getf("wdr", 0.4f)); });
        run("11_gamma", [&] {
            isp::stage11_gamma(img, !a.has("manual"), a.getf("ev", 0.f));
        });
        run("12_color_space", [&] { isp::stage12_color_space(img); });
        run("13_nr_luma", [&] { isp::stage13_nr_luma(img, a.getf("nr-luma", 0.012f)); });
        run("14_edge_enhance", [&] { isp::stage14_edge_enhance(img, a.getf("edge", 0.4f)); });
        run("15_contrast_brightness", [&] {
            isp::stage15_contrast_brightness(img, a.getf("contrast", 1.05f),
                                             a.getf("brightness", 0.005f));
        });
        run("16_nr_chroma", [&] { isp::stage16_nr_chroma(img, a.getf("nr-chroma", 0.4f)); });
        run("17_hue_saturation", [&] {
            isp::stage17_hue_saturation(img, a.getf("hue", 0.f), a.getf("sat", 1.08f));
        });
        run("18_scale_crop", [&] {
            isp::stage18_scale_crop(img, a.getf("scale", 0.5f), !a.has("no-crop"));
        });
        isp::Timer t19;
        isp::stage19_encoder(img, out, yuv);
        times.push_back({"19_encoder", t19.ms()});

        double total = 0;
        std::printf("\n============================================================\n");
        for (const auto& p : times) {
            std::printf("   %-24s %8.1f ms\n", p.first.c_str(), p.second);
            total += p.second;
        }
        std::printf("   %-24s %8.1f ms\n", "TOTAL", total);
        std::printf(" 输出: %s (%ux%u)\n", out.c_str(), img.width, img.height);
        std::printf("============================================================\n");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "错误: %s\n", e.what());
        return 1;
    }
    return 0;
}
