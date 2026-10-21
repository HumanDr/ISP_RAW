#include "isp/raw.h"
#include "isp/stages.h"

namespace isp {

void stage00_raw_load(const std::string& raw_path, Image& out,
                      const std::string& meta_path) {
    out = load_raw(raw_path, meta_path);
}

}  // namespace isp
