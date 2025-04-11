#include "video_processor.h"
#include <string>
#include <vector>
#include <sstream>
#include <cstdlib>

bool process_video(
    const char* input_path,
    const char* output_path,
    const char* resolution,
    const char* aspect_ratio,
    const char* background_music,
    float volume,
    const char* font,
    int font_size,
    const char* text_color,
    const char** icons,
    int icon_count
) {
    // Construct FFmpeg command
    std::stringstream cmd;
    cmd << "ffmpeg -i \"" << input_path << "\" ";

    // Add background music if provided
    if (background_music && std::string(background_music) != "") {
        cmd << "-i \"" << background_music << "\" -filter_complex \"[1:a]volume=" << volume << "[a1];[0:a][a1]amix=inputs=2:duration=first:dropout_transition=2\" ";
    }

    // Add text overlay (placeholder text "Sample Text")
    cmd << "-vf \"drawtext=fontfile='" << font << "':text='Sample Text':fontcolor=" << text_color << ":fontsize=" << font_size << ":x=(w-text_w)/2:y=(h-text_h)/2,";

    // Add aspect ratio and resolution
    cmd << "scale=" << resolution << ":force_original_aspect_ratio=decrease,pad=" << resolution << ":(ow-iw)/2:(oh-ih)/2\" ";

    // Add logo overlays
    for (int i = 0; i < icon_count; i++) {
        cmd << "-i \"" << icons[i] << "\" ";
    }
    if (icon_count > 0) {
        cmd << "-filter_complex \"";
        for (int i = 0; i < icon_count; i++) {
            cmd << "[" << (i + 1) << ":v]scale=50:50[logo" << i << "];";
        }
        for (int i = 0; i < icon_count; i++) {
            cmd << "[0:v][logo" << i << "]overlay=10:" << (10 + i * 60) << (i == icon_count - 1 ? "\"" : ",");
        }
    }

    // Output settings
    cmd << "-c:v libx264 -c:a aac -y \"" << output_path << "\"";

    // Execute FFmpeg command
    int result = system(cmd.str().c_str());
    return result == 0;
}

bool trim_video(
    const char* input_path,
    const char* output_path,
    float start_time,
    float end_time
) {
    // Construct FFmpeg command for trimming
    std::stringstream cmd;
    cmd << "ffmpeg -i \"" << input_path << "\" -ss " << start_time << " -to " << end_time << " -c:v libx264 -c:a aac -y \"" << output_path << "\"";

    // Execute FFmpeg command
    int result = system(cmd.str().c_str());
    return result == 0;
}