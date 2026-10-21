#include "isp/raw.h"

#include <cstdio>
#include <cstring>
#include <fstream>
#include <sstream>
#include <stdexcept>

namespace isp {
namespace {
Cfa parse_cfa(const std::string& s) {
    if (s == "RGGB") return CFA_RGGB;
    if (s == "BGGR") return CFA_BGGR;
    if (s == "GRBG") return CFA_GRBG;
    if (s == "GBRG") return CFA_GBRG;
    throw std::runtime_error("meta 里的 bayer 只能是 RGGB/BGGR/GRBG/GBRG");
}
}  // namespace

RawMeta load_raw_meta(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("打不开 meta: " + path);
    RawMeta m;
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::istringstream ss(line);
        std::string key;
        ss >> key;
        if (key == "width") ss >> m.width;
        else if (key == "height") ss >> m.height;
        else if (key == "bayer") ss >> m.bayer;
        else if (key == "white") ss >> m.white;
        else if (key == "camera") {
            std::getline(ss, m.camera);
            while (!m.camera.empty() && (m.camera[0] == ' ' || m.camera[0] == '\t'))
                m.camera.erase(m.camera.begin());
        } else if (key == "black") {
            for (int i = 0; i < 4; ++i) ss >> m.black[i];
        } else if (key == "wb") {
            for (int i = 0; i < 3; ++i) ss >> m.wb[i];
        } else if (key == "cam_to_xyz") {
            for (int i = 0; i < 9; ++i) ss >> m.cam_to_xyz[i];
        }
    }
    if (m.width <= 0 || m.height <= 0)
        throw std::runtime_error("meta 缺少 width/height: " + path);
    return m;
}

Image load_raw(const std::string& raw_path, const std::string& meta_path) {
    std::string mp = meta_path;
    if (mp.empty()) {
        const size_t dot = raw_path.find_last_of('.');
        mp = (dot == std::string::npos ? raw_path : raw_path.substr(0, dot)) + ".meta";
    }
    const RawMeta m = load_raw_meta(mp);

    const size_t need = static_cast<size_t>(m.width) * m.height * 2;
    std::ifstream in(raw_path, std::ios::binary);
    if (!in) throw std::runtime_error("打不开 raw: " + raw_path);
    in.seekg(0, std::ios::end);
    const size_t size = static_cast<size_t>(in.tellg());
    in.seekg(0);
    if (size != need) {
        throw std::runtime_error(
            "raw 文件大小不对：期望 " + std::to_string(need) + " 字节（" +
            std::to_string(m.width) + "x" + std::to_string(m.height) +
            "x2），实际 " + std::to_string(size) + " 字节");
    }

    Image img;
    img.allocate(DT_U16, m.width, m.height, 1);
    img.cfa = parse_cfa(m.bayer);
    for (int i = 0; i < 4; ++i) img.black[i] = static_cast<float>(m.black[i]);
    img.white = static_cast<float>(m.white);
    for (int i = 0; i < 3; ++i) img.wb[i] = m.wb[i];
    for (int i = 0; i < 9; ++i) img.cam_to_xyz[i] = m.cam_to_xyz[i];
    img.camera = m.camera;
    img.bit_depth = 16;
    img.note = "raw: " + std::to_string(m.width) + "x" + std::to_string(m.height) +
               " " + m.bayer + " black " + std::to_string(m.black[0]);

    in.read(reinterpret_cast<char*>(img.pix_u16()), need);
    if (!in) throw std::runtime_error("raw 读取不完整");
    return img;
}

}  // namespace isp
