import os
import subprocess
import re
import whisper
from transformers import pipeline

def extract_audio(video_path, audio_path):
    cmd = ['ffmpeg', '-i', video_path, '-vn', '-acodec', 'mp3', audio_path, '-y']
    subprocess.run(cmd, check=True)

def generate_subtitles(video_path, language):
    audio_path = os.path.join('temp', 'audio.mp3')
    extract_audio(video_path, audio_path)
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    subtitles = []
    for segment in result["segments"]:
        start = f"{int(segment['start']//3600):02d}:{int((segment['start']%3600)//60):02d}:{segment['start']%60:06.3f}".replace('.', ',')
        end = f"{int(segment['end']//3600):02d}:{int((segment['end']%3600)//60):02d}:{segment['end']%60:06.3f}".replace('.', ',')
        text = segment['text']
        subtitles.append((start, end, text))
    os.remove(audio_path)
    return translate_subtitles(subtitles, language)

def translate_subtitles(subtitles, target_language):
    lang_map = {'English': 'en', 'Vietnamese': 'vi', 'Japanese': 'ja'}
    target_lang = lang_map.get(target_language, 'en')
    if target_lang != 'en':
        translator = pipeline("translation", model=f"Helsinki-NLP/opus-mt-en-{target_lang}")
        translated = []
        for start, end, text in subtitles:
            translated_text = translator(text)[0]['translation_text']
            translated.append((start, end, translated_text))
        return translated
    return subtitles