import os
import ctypes
import logging

# Load the C++ shared library
try:
    video_processor_lib = ctypes.CDLL(os.path.join(os.path.dirname(__file__), '..', 'cpp', 'build', 'video_processor.dll'))
except Exception as e:
    logging.error(f"Failed to load video_processor.dll: {str(e)}")
    raise

# Define function signatures
video_processor_lib.process_video.argtypes = [
    ctypes.c_char_p,  # input_path
    ctypes.c_char_p,  # output_path
    ctypes.c_char_p,  # resolution
    ctypes.c_char_p,  # aspect_ratio
    ctypes.c_char_p,  # background_music
    ctypes.c_float,   # volume
    ctypes.c_char_p,  # font
    ctypes.c_int,     # font_size
    ctypes.c_char_p,  # text_color
    ctypes.POINTER(ctypes.c_char_p),  # icons
    ctypes.c_int      # icon_count
]
video_processor_lib.process_video.restype = ctypes.c_bool

video_processor_lib.trim_video.argtypes = [
    ctypes.c_char_p,  # input_path
    ctypes.c_char_p,  # output_path
    ctypes.c_float,   # start_time
    ctypes.c_float    # end_time
]
video_processor_lib.trim_video.restype = ctypes.c_bool

def process_video(input_path, output_path, resolution, aspect_ratio, background_music, volume, font, font_size, text_color, icons):
    """
    Process video using C++ library.
    Args:
        input_path (str): Path to input video.
        output_path (str): Path to output video.
        resolution (str): Resolution (e.g., "1280:720").
        aspect_ratio (str): Aspect ratio (e.g., "16:9").
        background_music (str): Path to background music.
        volume (float): Volume level (0.0 to 2.0).
        font (str): Font name.
        font_size (int): Font size.
        text_color (str): Text color (e.g., "white").
        icons (list): List of logo paths.
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        input_path = input_path.encode('utf-8')
        output_path = output_path.encode('utf-8')
        resolution = resolution.encode('utf-8')
        aspect_ratio = aspect_ratio.encode('utf-8')
        background_music = background_music.encode('utf-8') if background_music else b""
        font = font.encode('utf-8')
        text_color = text_color.encode('utf-8')

        # Convert icons list to C array
        icon_count = len(icons)
        icon_array = (ctypes.c_char_p * icon_count)(*[icon.encode('utf-8') for icon in icons])

        return video_processor_lib.process_video(
            input_path, output_path, resolution, aspect_ratio,
            background_music, volume, font, font_size, text_color,
            icon_array, icon_count
        )
    except Exception as e:
        logging.error(f"Error processing video: {str(e)}")
        return False

def trim_video(input_path, output_path, start_time, end_time):
    """
    Trim video using C++ library.
    Args:
        input_path (str): Path to input video.
        output_path (str): Path to output video.
        start_time (float): Start time in seconds.
        end_time (float): End time in seconds.
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        input_path = input_path.encode('utf-8')
        output_path = output_path.encode('utf-8')
        return video_processor_lib.trim_video(input_path, output_path, start_time, end_time)
    except Exception as e:
        logging.error(f"Error trimming video: {str(e)}")
        return False