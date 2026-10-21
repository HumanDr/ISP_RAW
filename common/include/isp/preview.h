// =============================================================================
//  preview.h  --  把任意 stage 的 .isp 转成"人眼能看"的 8bit 预览
//  注意：预览只是为了观察，不是 pipeline 的一部分。线性数据必须先做 gamma，
//  否则看起来会很暗，这是新手最常见的困惑之一。
// =============================================================================
#pragma once

#include <cstdint>
#include <vector>

#include "isp/image.h"

namespace isp {

struct PreviewOptions {
    float gamma = 2.2f;      // 显示 gamma；线性数据用 2.2，已编码数据用 1.0
    float ev = 0.f;          // 曝光补偿（档）
    bool auto_stretch = true;
    float lo_pct = 0.1f;     // 自动拉伸的下分位
    float hi_pct = 99.5f;    // 自动拉伸的上分位
};

struct Preview {
    int width = 0;
    int height = 0;
    int channels = 3;  // Bayer 预览输出 1 通道灰度
    std::vector<uint8_t> data;
};

Preview make_preview(const Image& img, const PreviewOptions& opt);

}  // namespace isp
