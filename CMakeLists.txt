cmake_minimum_required(VERSION 3.16)
project(isp_raw_course LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "" FORCE)
endif()

find_package(PNG REQUIRED)

add_library(isp_core STATIC
  common/src/image.cpp
  common/src/raw.cpp
  common/src/io.cpp
  common/src/preview.cpp
  common/src/cli.cpp
  stages/00_raw_load/stage.cpp
  stages/01_blc/stage.cpp
  stages/02_lsc/stage.cpp
  stages/03_dpc/stage.cpp
  stages/04_nr_raw/stage.cpp
  stages/05_awb/stage.cpp
  stages/06_demosaic/stage.cpp
  stages/07_nr_color/stage.cpp
  stages/08_xtalk/stage.cpp
  stages/09_color_correction/stage.cpp
  stages/10_hdr_wdr/stage.cpp
  stages/11_gamma/stage.cpp
  stages/12_color_space/stage.cpp
  stages/13_nr_luma/stage.cpp
  stages/14_edge_enhance/stage.cpp
  stages/15_contrast_brightness/stage.cpp
  stages/16_nr_chroma/stage.cpp
  stages/17_hue_saturation/stage.cpp
  stages/18_scale_crop/stage.cpp
  stages/19_encoder/stage.cpp
)
target_include_directories(isp_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/common/include)
target_link_libraries(isp_core PUBLIC PNG::PNG)
target_compile_options(isp_core PRIVATE -O2 -Wall -Wextra)

function(add_isp_tool name source)
  add_executable(${name} ${source})
  target_link_libraries(${name} PRIVATE isp_core)
endfunction()

add_isp_tool(isp_00_raw_load stages/00_raw_load/main.cpp)
add_isp_tool(isp_01_blc stages/01_blc/main.cpp)
add_isp_tool(isp_02_lsc stages/02_lsc/main.cpp)
add_isp_tool(isp_03_dpc stages/03_dpc/main.cpp)
add_isp_tool(isp_04_nr_raw stages/04_nr_raw/main.cpp)
add_isp_tool(isp_05_awb stages/05_awb/main.cpp)
add_isp_tool(isp_06_demosaic stages/06_demosaic/main.cpp)
add_isp_tool(isp_07_nr_color stages/07_nr_color/main.cpp)
add_isp_tool(isp_08_xtalk stages/08_xtalk/main.cpp)
add_isp_tool(isp_09_color_correction stages/09_color_correction/main.cpp)
add_isp_tool(isp_10_hdr_wdr stages/10_hdr_wdr/main.cpp)
add_isp_tool(isp_11_gamma stages/11_gamma/main.cpp)
add_isp_tool(isp_12_color_space stages/12_color_space/main.cpp)
add_isp_tool(isp_13_nr_luma stages/13_nr_luma/main.cpp)
add_isp_tool(isp_14_edge_enhance stages/14_edge_enhance/main.cpp)
add_isp_tool(isp_15_contrast_brightness stages/15_contrast_brightness/main.cpp)
add_isp_tool(isp_16_nr_chroma stages/16_nr_chroma/main.cpp)
add_isp_tool(isp_17_hue_saturation stages/17_hue_saturation/main.cpp)
add_isp_tool(isp_18_scale_crop stages/18_scale_crop/main.cpp)
add_isp_tool(isp_19_encoder stages/19_encoder/main.cpp)

add_isp_tool(isp_pipeline apps/isp_pipeline.cpp)
add_isp_tool(isp_dump apps/isp_dump.cpp)
add_isp_tool(isp_info apps/isp_info.cpp)
add_isp_tool(isp_ae_af apps/isp_ae_af.cpp)
