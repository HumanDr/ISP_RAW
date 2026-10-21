// =============================================================================
//  cli.h  --  每个 stage 的小工具共用：参数解析、统计打印、计时
// =============================================================================
#pragma once

#include <chrono>
#include <map>
#include <string>
#include <vector>

#include "isp/image.h"

namespace isp {

struct Args {
    std::string in;
    std::string out;
    std::vector<std::string> pos;
    std::map<std::string, std::string> opt;

    bool has(const std::string& k) const { return opt.count(k) != 0; }
    std::string get(const std::string& k, const std::string& def = "") const {
        auto it = opt.find(k);
        return it == opt.end() ? def : it->second;
    }
    int geti(const std::string& k, int def) const;
    float getf(const std::string& k, float def) const;
};

// 用法：tool <输入> <输出> [--key value] [--flag]
Args parse_args(int argc, char** argv, const std::string& usage,
                bool require_input = true);

// 打印尺寸/类型/分位数/裁剪比例，方便每一步对比。
void print_stats(const Image& img, const char* tag);

class Timer {
public:
    Timer() : t0_(std::chrono::steady_clock::now()) {}
    void reset() { t0_ = std::chrono::steady_clock::now(); }
    double ms() const {
        return std::chrono::duration<double, std::milli>(
                   std::chrono::steady_clock::now() - t0_)
            .count();
    }

private:
    std::chrono::steady_clock::time_point t0_;
};

}  // namespace isp
