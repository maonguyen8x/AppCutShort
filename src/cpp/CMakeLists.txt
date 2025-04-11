cmake_minimum_required(VERSION 3.10)
project(video_processor)

# Set C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Find FFmpeg
find_path(FFMPEG_INCLUDE_DIR libavcodec/avcodec.h)
find_library(FFMPEG_LIB avcodec)
if(NOT FFMPEG_INCLUDE_DIR OR NOT FFMPEG_LIB)
    message(FATAL_ERROR "FFmpeg not found. Please install FFmpeg development libraries.")
endif()

# Add source files
add_library(video_processor SHARED video_processor.cpp)

# Include directories
target_include_directories(video_processor PRIVATE ${FFMPEG_INCLUDE_DIR})

# Link libraries
target_link_libraries(video_processor PRIVATE ${FFMPEG_LIB})

# Set output directory
set_target_properties(video_processor PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/build"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/build"
)