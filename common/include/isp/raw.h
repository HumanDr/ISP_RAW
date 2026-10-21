// =============================================================================
//  raw.h  --  读取“纯 .raw + 同名 .meta”的传感器数据
//
//  纯 .raw 只有像素，没有宽高/CFA/黑电平，所以旁边必须有一个 .meta。
//  格式刻意做得极简，一行一个字段：
//
//      width 5760
//      height 3840
//      bayer RGGB
//      black 2047 2047 2047 2048
//      white 15000
//      wb 1.649 1.000 2.165
//      cam_to_xyz 0.7385 -0.0108 0.2229 ...
//      camera Canon EOS 5D Mark III
//
//  这样你可以用记事本改参数，而不需要重新编译。
// =============================================================================
#pragma once

#include <string>

#include "isp/image.h"

namespace isp {

struct RawMeta {
    int width = 0;
    int height = 0;
    std::string bayer = "RGGB";
    int black[4] = {0, 0, 0, 0};
    int white = 65535;
    float wb[3] = {1.f, 1.f, 1.f};
    float cam_to_xyz[9] = {1, 0, 0, 0, 1, 0, 0, 0, 1};
    std::string camera = "unknown";
};

RawMeta load_raw_meta(const std::string& meta_path);

// raw_path 是 16bit little-endian、无文件头的 Bayer 数据；
// meta_path 为空时自动找同名 .meta。
Image load_raw(const std::string& raw_path, const std::string& meta_path = "");

}  // namespace isp
