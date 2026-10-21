#include "isp/image.h"

#include <cstdio>
#include <cstring>
#include <stdexcept>

namespace isp {

const char* cfa_name(Cfa c) {
    switch (c) {
        case CFA_RGGB: return "RGGB";
        case CFA_BGGR: return "BGGR";
        case CFA_GRBG: return "GRBG";
        case CFA_GBRG: return "GBRG";
        default: return "NONE";
    }
}

const char* dtype_name(DType t) { return t == DT_U16 ? "u16" : "f32"; }

void Image::allocate(DType dt, int w, int h, int ch) {
    if (w <= 0 || h <= 0 || (ch != 1 && ch != 3))
        throw std::runtime_error("Image::allocate 参数非法");
    dtype = dt;
    width = static_cast<uint32_t>(w);
    height = static_cast<uint32_t>(h);
    channels = static_cast<uint32_t>(ch);
    data.assign(expected_bytes(), 0);
    if (channels == 3 && cfa != CFA_NONE) cfa = CFA_NONE;
}

void Image::require_f32() {
    if (dtype == DT_F32) return;
    if (data.size() != expected_bytes())
        throw std::runtime_error("Image::require_f32: 数据长度不匹配");
    const uint16_t* src = pix_u16();
    std::vector<float> dst(sample_count());
    for (size_t i = 0; i < dst.size(); ++i) dst[i] = static_cast<float>(src[i]);
    data.resize(dst.size() * sizeof(float));
    std::memcpy(data.data(), dst.data(), data.size());
    dtype = DT_F32;
}

float Image::at(int x, int y, int c) const {
    if (x < 0 || y < 0 || x >= static_cast<int>(width) ||
        y >= static_cast<int>(height) || c < 0 || c >= static_cast<int>(channels))
        throw std::runtime_error("Image::at 越界");
    const size_t idx = (static_cast<size_t>(y) * width + x) * channels + c;
    return (dtype == DT_U16) ? static_cast<float>(pix_u16()[idx]) : pix_f32()[idx];
}

void Image::set(int x, int y, int c, float v) {
    if (x < 0 || y < 0 || x >= static_cast<int>(width) ||
        y >= static_cast<int>(height) || c < 0 || c >= static_cast<int>(channels))
        throw std::runtime_error("Image::set 越界");
    const size_t idx = (static_cast<size_t>(y) * width + x) * channels + c;
    if (dtype == DT_U16)
        pix_u16()[idx] = static_cast<uint16_t>(v + 0.5f);
    else
        pix_f32()[idx] = v;
}

int Image::cfa_color(int x, int y) const {
    // 2x2 排列查表：行优先 (0,0),(1,0),(0,1),(1,1)
    static const int table[4][4] = {
        {0, 1, 1, 2},  // RGGB
        {2, 1, 1, 0},  // BGGR
        {1, 0, 2, 1},  // GRBG
        {1, 2, 0, 1},  // GBRG
    };
    if (cfa == CFA_NONE || cfa > CFA_GBRG) return 0;
    return table[cfa][cfa_pos(x, y)];
}

// -----------------------------------------------------------------------------
//  .isp 读写
// -----------------------------------------------------------------------------
static void copy_str(char* dst, size_t n, const std::string& s) {
    std::memset(dst, 0, n);
    std::strncpy(dst, s.c_str(), n - 1);
}

static std::string from_str(const char* s, size_t n) {
    size_t len = 0;
    while (len < n && s[len]) ++len;
    return std::string(s, len);
}

void save_isp(const std::string& path, const Image& img) {
    if (img.data.size() != img.expected_bytes())
        throw std::runtime_error("save_isp: 像素数据长度与头信息不一致");

    IspFileHeader h{};
    std::memcpy(h.magic, "ISPIMG1", 7);
    h.version = 1;
    h.width = img.width;
    h.height = img.height;
    h.channels = img.channels;
    h.cfa = static_cast<uint32_t>(img.cfa);
    h.dtype = static_cast<uint32_t>(img.dtype);
    h.bit_depth = img.bit_depth;
    h.space = static_cast<uint32_t>(img.space);
    h.data_bytes = img.data.size();
    for (int i = 0; i < 4; ++i) h.black[i] = img.black[i];
    h.white = img.white;
    for (int i = 0; i < 3; ++i) h.wb[i] = img.wb[i];
    for (int i = 0; i < 9; ++i) h.cam_to_xyz[i] = img.cam_to_xyz[i];
    h.exposure = img.exposure;
    h.gamma = img.gamma;
    copy_str(h.camera, sizeof(h.camera), img.camera);
    copy_str(h.note, sizeof(h.note), img.note);

    FILE* fp = std::fopen(path.c_str(), "wb");
    if (!fp) throw std::runtime_error("无法写入文件: " + path);
    if (std::fwrite(&h, sizeof(h), 1, fp) != 1 ||
        std::fwrite(img.data.data(), 1, img.data.size(), fp) != img.data.size()) {
        std::fclose(fp);
        throw std::runtime_error("写入失败（磁盘满？）: " + path);
    }
    std::fclose(fp);
}

IspFileHeader read_isp_header(const std::string& path) {
    FILE* fp = std::fopen(path.c_str(), "rb");
    if (!fp) throw std::runtime_error("无法打开文件: " + path);
    IspFileHeader h{};
    size_t n = std::fread(&h, sizeof(h), 1, fp);
    std::fclose(fp);
    if (n != 1) throw std::runtime_error("文件太小，不是 .isp: " + path);
    if (std::memcmp(h.magic, "ISPIMG1", 7) != 0)
        throw std::runtime_error("magic 不对，不是 .isp 文件: " + path);
    return h;
}

Image load_isp(const std::string& path) {
    IspFileHeader h = read_isp_header(path);
    if (h.version != 1) throw std::runtime_error("不支持的 .isp 版本");

    Image img;
    img.width = h.width;
    img.height = h.height;
    img.channels = h.channels;
    img.cfa = static_cast<Cfa>(h.cfa);
    img.dtype = static_cast<DType>(h.dtype);
    img.bit_depth = h.bit_depth;
    img.space = static_cast<Space>(h.space);
    for (int i = 0; i < 4; ++i) img.black[i] = h.black[i];
    img.white = h.white;
    for (int i = 0; i < 3; ++i) img.wb[i] = h.wb[i];
    for (int i = 0; i < 9; ++i) img.cam_to_xyz[i] = h.cam_to_xyz[i];
    img.exposure = h.exposure;
    img.gamma = h.gamma;
    img.camera = from_str(h.camera, sizeof(h.camera));
    img.note = from_str(h.note, sizeof(h.note));

    if (h.data_bytes != img.expected_bytes())
        throw std::runtime_error("头信息里的 data_bytes 与尺寸不匹配: " + path);

    img.data.resize(h.data_bytes);
    FILE* fp = std::fopen(path.c_str(), "rb");
    if (!fp) throw std::runtime_error("无法打开文件: " + path);
    std::fseek(fp, sizeof(IspFileHeader), SEEK_SET);
    size_t got = std::fread(img.data.data(), 1, img.data.size(), fp);
    std::fclose(fp);
    if (got != img.data.size())
        throw std::runtime_error("像素数据读取不完整（文件被截断？）: " + path);
    return img;
}

}  // namespace isp
