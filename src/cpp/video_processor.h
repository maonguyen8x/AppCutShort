#ifndef VIDEO_PROCESSOR_H
#define VIDEO_PROCESSOR_H

#include <string>

extern "C" {
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
    );

    bool trim_video(
        const char* input_path,
        const char* output_path,
        float start_time,
        float end_time
    );
}

#endif // VIDEO_PROCESSOR_H