#!/usr/bin/env bash
# 一键跑通：.raw -> 20 个 stage -> PNG
#   ./run_pipeline.sh              内存流水线，输出 out/final.png
#   ./run_pipeline.sh --keep       同时保存每一步 .isp 到 out/stage/
#   ./run_pipeline.sh --steps      每个 stage 一个进程，走 out/steps/
set -euo pipefail
cd "$(dirname "$0")"

[ -x build/isp_pipeline ] || ./build.sh

MODE=pipeline
ARGS=()
for a in "$@"; do
    if [ "$a" = "--steps" ]; then MODE=steps; else ARGS+=("$a"); fi
done

if [ "$MODE" = pipeline ]; then
    ./build/isp_pipeline --raw data/sample.raw --meta data/sample.meta \
        --out out/final.png "${ARGS[@]}"
    echo
    echo "输出: out/final.png"
    exit 0
fi

S=out/steps
mkdir -p "$S"
./build/isp_00_raw_load data/sample.raw "$S/00_raw_load.isp" --meta data/sample.meta
./build/isp_01_blc "$S/00_raw_load.isp" "$S/01_blc.isp"
./build/isp_02_lsc "$S/01_blc.isp" "$S/02_lsc.isp"
./build/isp_03_dpc "$S/02_lsc.isp" "$S/03_dpc.isp"
./build/isp_04_nr_raw "$S/03_dpc.isp" "$S/04_nr_raw.isp"
./build/isp_05_awb "$S/04_nr_raw.isp" "$S/05_awb.isp" --strength 0.5
./build/isp_06_demosaic "$S/05_awb.isp" "$S/06_demosaic.isp"
./build/isp_07_nr_color "$S/06_demosaic.isp" "$S/07_nr_color.isp" --strength 0.4
./build/isp_08_xtalk "$S/07_nr_color.isp" "$S/08_xtalk.isp"
./build/isp_09_color_correction "$S/08_xtalk.isp" "$S/09_color_correction.isp"
./build/isp_10_hdr_wdr "$S/09_color_correction.isp" "$S/10_hdr_wdr.isp" --strength 0.4
./build/isp_11_gamma "$S/10_hdr_wdr.isp" "$S/11_gamma.isp"
./build/isp_12_color_space "$S/11_gamma.isp" "$S/12_color_space.isp"
./build/isp_13_nr_luma "$S/12_color_space.isp" "$S/13_nr_luma.isp" --sigma 0.012
./build/isp_14_edge_enhance "$S/13_nr_luma.isp" "$S/14_edge_enhance.isp" --amount 0.4
./build/isp_15_contrast_brightness "$S/14_edge_enhance.isp" "$S/15_contrast_brightness.isp" --contrast 1.05 --brightness 0.005
./build/isp_16_nr_chroma "$S/15_contrast_brightness.isp" "$S/16_nr_chroma.isp" --strength 0.4
./build/isp_17_hue_saturation "$S/16_nr_chroma.isp" "$S/17_hue_saturation.isp" --sat 1.08
./build/isp_18_scale_crop "$S/17_hue_saturation.isp" "$S/18_scale_crop.isp" --scale 0.5 --crop
./build/isp_19_encoder "$S/18_scale_crop.isp" out/final_steps.png --yuv
echo
echo "输出: out/final_steps.png"
