import os
import subprocess
import re
import whisper
import torch
from transformers import pipeline
import warnings
import platform
import logging
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='appcutshort.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress FP16 warnings if not needed
warnings.filterwarnings("ignore", category=UserWarning, message="FP16 is not supported on CPU")

def extract_audio(video_path, audio_path, progress_callback=None):
    # Check if video_path is a URL (streaming) or local file
    try:
        if video_path.startswith('http'):
            # Extract audio directly from the streaming URL
            cmd = ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'mp3', audio_path, '-y']
        else:
            # Extract audio from a local file
            cmd = ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'mp3', audio_path, '-y']

        # Run FFmpeg and capture progress
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )

        duration = None
        ffmpeg_output = []
        for line in process.stdout:
            ffmpeg_output.append(line)
            if 'Duration' in line and duration is None:
                match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', line)
                if match:
                    hours, minutes, seconds = map(float, match.groups())
                    duration = hours * 3600 + minutes * 60 + seconds
            if 'time=' in line and duration:
                match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                if match:
                    hours, minutes, seconds = map(float, match.groups())
                    current_time = hours * 3600 + minutes * 60 + seconds
                    percent = int((current_time / duration) * 50) if duration > 0 else 0  # 50% for audio extraction
                    if progress_callback:
                        progress_callback(min(percent, 50))

        process.wait()
        if process.returncode != 0:
            error_message = "Error extracting audio. FFmpeg failed.\n" + "\n".join(ffmpeg_output[-10:])
            logging.error(error_message)
            return False

        logging.info("Audio extracted successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error extracting audio: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error extracting audio: {e}")
        return False

def get_font_path():
    # Determine font path based on OS
    if os.name == 'nt':  # Windows
        return 'C:\\Windows\\Fonts\\arial.ttf'
    elif platform.system() == 'Darwin':  # macOS
        return '/Library/Fonts/Arial.ttf'
    else:  # Linux
        return '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def generate_subtitles(video_path, language, progress_callback=None):
    audio_path = os.path.join('temp', 'audio.mp3')
    os.makedirs('temp', exist_ok=True)

    # Step 1: Extract audio (0-50%)
    if not extract_audio(video_path, audio_path, progress_callback):
        raise Exception("Failed to extract audio from video")

    # Step 2: Transcribe audio (50-100%)
    try:
        if progress_callback:
            progress_callback(50)  # Audio extraction complete
        model = whisper.load_model("tiny")

        # Simulate progress during transcription (since whisper doesn't provide progress updates)
        start_time = time.time()
        result = model.transcribe(audio_path)
        end_time = time.time()

        # Simulate progress updates (linearly from 50% to 100%)
        duration = end_time - start_time
        if duration > 0 and progress_callback:
            for i in range(51, 101):
                time.sleep(duration / 50)  # Simulate progress over time
                progress_callback(i)
    except Exception as e:
        raise Exception(f"Failed to transcribe audio: {e}")
    finally:
        # Clean up the temporary audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)

    subtitles = []
    for segment in result["segments"]:
        start = f"{int(segment['start']//3600):02d}:{int((segment['start']%3600)//60):02d}:{segment['start']%60:06.3f}".replace('.', ',')
        end = f"{int(segment['end']//3600):02d}:{int((segment['end']%3600)//60):02d}:{segment['end']%60:06.3f}".replace('.', ',')
        text = segment['text'].strip()
        if text:  # Only add non-empty text
            subtitles.append((start, end, text))

    return translate_subtitles(subtitles, language)

def translate_subtitles(subtitles, target_language):
    lang_map = {'English': 'en', 'Vietnamese': 'vi', 'Japanese': 'ja'}
    target_lang = lang_map.get(target_language, 'en')
    if target_lang != 'en':
        try:
            translator = pipeline("translation", model=f"Helsinki-NLP/opus-mt-en-{target_lang}")
            translated = []
            for start, end, text in subtitles:
                translated_text = translator(text)[0]['translation_text']
                translated.append((start, end, translated_text))
            return translated
        except Exception as e:
            logging.error(f"Error translating subtitles: {e}")
            return subtitles
    return subtitles