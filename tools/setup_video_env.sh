#!/usr/bin/env bash
# 为 tools/make_video.py 准备配音/编码环境。
# 不需要 root：所有 Python 包装在仓库内的 .pylibs/。
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p .pylibs out
export PYTHONPATH="$PWD/.pylibs"

if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "==> 安装 pip 到 .pylibs"
    curl -fsSL https://bootstrap.pypa.io/get-pip.py -o out/get-pip.py
    python3 out/get-pip.py --target "$PWD/.pylibs" --no-warn-script-location
    rm -f out/get-pip.py
fi

echo "==> 安装 edge-tts + imageio-ffmpeg"
python3 -m pip install --target "$PWD/.pylibs" --upgrade \
    edge-tts imageio-ffmpeg

echo "==> 检查"
python3 - <<'EOF'
import edge_tts, imageio_ffmpeg
print("edge-tts:", getattr(edge_tts, "__version__", "ok"))
print("ffmpeg  :", imageio_ffmpeg.get_ffmpeg_exe())
EOF

echo
echo "完成。运行：python3 tools/make_video.py"
