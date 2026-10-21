#include "isp/cli.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>

namespace isp {

int Args::geti(const std::string& k, int def) const {
    auto it = opt.find(k);
    if (it == opt.end()) return def;
    return std::atoi(it->second.c_str());
}

float Args::getf(const std::string& k, float def) const {
    auto it = opt.find(k);
    if (it == opt.end()) return def;
    return static_cast<float>(std::atof(it->second.c_str()));
}

Args parse_args(int argc, char** argv, const std::string& usage,
                bool require_input) {
    Args a;
    for (int i = 1; i < argc; ++i) {
        std::string s = argv[i];
        if (s == "-h" || s == "--help") {
            std::printf("%s\n", usage.c_str());
            std::exit(0);
        }
        if (s.rfind("--", 0) == 0) {
            std::string key = s.substr(2);
            std::string val;
            size_t eq = key.find('=');
            if (eq != std::string::npos) {
                val = key.substr(eq + 1);
                key = key.substr(0, eq);
            } else if (i + 1 < argc && std::string(argv[i + 1]).rfind("--", 0) != 0) {
                val = argv[++i];
            } else {
                val = "1";
            }
            a.opt[key] = val;
        } else {
            a.pos.push_back(s);
        }
    }
    if (a.pos.size() >= 1) a.in = a.pos[0];
    if (a.pos.size() >= 2) a.out = a.pos[1];
    if (require_input && a.in.empty())
        throw std::runtime_error("缺少输入文件\n" + usage);
    return a;
}

void print_stats(const Image& img, const char* tag) {
    const size_t n = img.sample_count();
    const size_t step = std::max<size_t>(1, n / 200000);
    std::printf("[%s] %ux%u c=%u %s %s | ", tag, img.width, img.height,
                img.channels, dtype_name(img.dtype), cfa_name(img.cfa));
    for (uint32_t c = 0; c < img.channels; ++c) {
        std::vector<float> v;
        double sum = 0;
        size_t cnt = 0, clipped = 0;
        float lo = 1e30f, hi = -1e30f;
        for (size_t i = c; i < n; i += step * img.channels) {
            float x = (img.dtype == DT_U16) ? static_cast<float>(img.pix_u16()[i])
                                            : img.pix_f32()[i];
            v.push_back(x);
            sum += x;
            ++cnt;
            lo = std::min(lo, x);
            hi = std::max(hi, x);
            if (x <= 0.f || x >= (img.dtype == DT_U16 ? img.white : 1.f)) ++clipped;
        }
        if (v.empty()) continue;
        std::sort(v.begin(), v.end());
        auto pc = [&](double p) { return v[static_cast<size_t>(p * (v.size() - 1))]; };
        if (img.channels > 1) std::printf("c%u ", c);
        std::printf("min %.1f p1 %.1f p50 %.1f p99 %.1f max %.1f mean %.1f clip %.2f%% | ",
                    lo, pc(0.01), pc(0.5), pc(0.99), hi, sum / cnt,
                    100.0 * clipped / cnt);
    }
    std::printf("\n");
    if (!img.note.empty()) std::printf("        note: %s\n", img.note.c_str());
}

}  // namespace isp
