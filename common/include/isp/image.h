// =============================================================================
//  image.h  --  ISP 教学流水线使用的图像容器与 .isp 中间文件格式
//
//  设计目标（对新手友好）：
//    * 一张图 = 头信息(metadata) + 一块连续的像素数据(data)
//    * Bayer RAW 是单通道(channels=1)，去马赛克之后是 3 通道(channels=3)
//    * 像素数据支持两种类型：
//        U16 : 传感器原始整数（0..65535），用于 stage 00
//        F32 : 归一化浮点（一般 0..1），用于后续所有 stage
//      这样既能"看见" RAW 的整数本质，又能避免反复量化。
//    * 所有 stage 之间用 .isp 文件传递，每一阶段都可以单独运行、单独观察。
// =============================================================================
#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace isp {

// CFA = Color Filter Array（彩色滤镜阵列）。
// 枚举值 0..3 表示 2x2 小块里四个位置的颜色排列，顺序是：
//   (0,0) (1,0)
//   (0,1) (1,1)
enum Cfa : uint32_t {
    CFA_RGGB = 0,  // 最常见的 Bayer 排列
    CFA_BGGR = 1,
    CFA_GRBG = 2,
    CFA_GBRG = 3,
    CFA_NONE = 0xFFFFFFFFu  // 三通道图像，无 CFA
};

enum DType : uint32_t { DT_U16 = 0, DT_F32 = 1 };

// 三通道数据当前所处的颜色空间：RGB 或 YUV(BT.709)
enum Space : uint32_t { SPACE_RGB = 0, SPACE_YUV = 1 };

// 一个"颜色"用 0=R, 1=G, 2=B 表示。
struct Image {
    uint32_t width = 0;
    uint32_t height = 0;
    uint32_t channels = 1;
    Cfa cfa = CFA_RGGB;
    DType dtype = DT_F32;
    Space space = SPACE_RGB;
    uint32_t bit_depth = 16;

    // Bayer 2x2 四个位置的暗电平（black level），顺序同 cfa_pos()。
    // 真实传感器的四个通道暗电平可能差 1~2 个 LSB，本例 Canon 5D3 是
    // {2047, 2047, 2047, 2048}。
    float black[4] = {0.f, 0.f, 0.f, 0.f};
    float white = 65535.f;  // 饱和电平（white level）

    // 白平衡增益，已归一化到 G=1。由 DNG 的 AsShotNeutral 计算而来。
    float wb[3] = {1.f, 1.f, 1.f};

    // 相机(已白平衡) RGB -> CIE XYZ(D65) 的 3x3 矩阵（行优先）。
    // 由 DNG 的 ForwardMatrix（或 ColorMatrix 求逆）+ Bradford 色适应得到。
    // 注意：它不是"相机 RGB -> sRGB"，stage 07 会再乘 XYZ->sRGB。
    float cam_to_xyz[9] = {1.f, 0.f, 0.f, 0.f, 1.f, 0.f, 0.f, 0.f, 1.f};

    float exposure = 1.f;  // 记录 stage 08 使用的曝光系数，便于观察
    float gamma = 1.f;     // 1=线性；sRGB 编码后也记为 1，仅作标记
    std::string camera;    // 相机型号
    std::string note;      // 一行备注（尺寸、CFA、来源等）

    std::vector<uint8_t> data;  // 像素字节；u16 或 f32

    size_t pixel_count() const {
        return static_cast<size_t>(width) * height;
    }
    size_t sample_count() const { return pixel_count() * channels; }
    size_t sample_bytes() const { return (dtype == DT_U16) ? 2 : 4; }
    size_t expected_bytes() const { return sample_count() * sample_bytes(); }

    uint16_t* pix_u16() { return reinterpret_cast<uint16_t*>(data.data()); }
    const uint16_t* pix_u16() const {
        return reinterpret_cast<const uint16_t*>(data.data());
    }
    float* pix_f32() { return reinterpret_cast<float*>(data.data()); }
    const float* pix_f32() const {
        return reinterpret_cast<const float*>(data.data());
    }

    // 重新分配一块像素内存（不清零，调用者负责填充）。
    void allocate(DType dt, int w, int h, int ch);

    // 把 U16 数据原地转换成 F32（数值不做归一化，仍是原始计数）。
    void require_f32();

    // 逐像素读写（慢，适合教学/边界代码；核心循环请用指针）。
    float at(int x, int y, int c = 0) const;
    void set(int x, int y, int c, float v);

    // 返回 (x,y) 处的颜色：0=R 1=G 2=B。三通道图直接返回 c。
    int cfa_color(int x, int y) const;
    int cfa_pos(int x, int y) const { return ((y & 1) << 1) | (x & 1); }

    bool is_bayer() const { return channels == 1 && cfa != CFA_NONE; }
    size_t bytes() const { return data.size(); }
};

const char* cfa_name(Cfa c);
const char* dtype_name(DType t);

// -----------------------------------------------------------------------------
//  .isp 中间文件：固定 284 字节头 + 纯像素数据（小端）。
//  用 xxd 或 `isp_info` 可以直接看头，方便调试。
// -----------------------------------------------------------------------------
Image load_isp(const std::string& path);
void save_isp(const std::string& path, const Image& img);

// 供 isp_info 使用：只读头，不读几十 MB 的像素。
// 必须 1 字节对齐，保证不同编译器/平台写出的 .isp 头完全一致。
#pragma pack(push, 1)
struct IspFileHeader {
    char magic[8];
    uint32_t version;
    uint32_t width, height, channels;
    uint32_t cfa, dtype, bit_depth, space;
    uint64_t data_bytes;
    float black[4];
    float white;
    float wb[3];
    float cam_to_xyz[9];
    float exposure, gamma;
    char camera[64];
    char note[96];
};
#pragma pack(pop)
static_assert(sizeof(IspFileHeader) == 284, "IspFileHeader 布局必须稳定");

IspFileHeader read_isp_header(const std::string& path);

}  // namespace isp
