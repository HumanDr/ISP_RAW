#!/usr/bin/env bash
# 改完 tools/script_text.py 后，一条命令重建 PPT + 视频 + 讲解词。
#
#   ./tools/rebuild_video.sh            # 复用没变的配音
#   ./tools/rebuild_video.sh --force    # 全部重新配音
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .pylibs ]; then
    echo "缺少 .pylibs，先运行 ./tools/setup_video_env.sh"
    exit 1
fi

python3 tools/make_ppt.py
python3 tools/make_video.py "$@"
python3 tools/make_script_doc.py

echo
echo "完成：docs/ISP_Raw_5min.mp4"
