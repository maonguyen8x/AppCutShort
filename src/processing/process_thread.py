import os
import subprocess
import re
import shutil
from PyQt6.QtCore import QThread, pyqtSignal

class ProcessThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, aspect_ratio, font, color, subtitles, language, duration):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.aspect_ratio = aspect_ratio
        self.font = font
        self.color = color
        self.subtitles = subtitles
        self.language = language
        self.duration = duration

    def run(self):
        try:
            if not shutil.which('ffmpeg'):
                self.error.emit("FFmpeg not found. Please install FFmpeg and add it to PATH.")
                return
            if not os.path.exists('temp'):
                os.makedirs('temp')
            if not os.path.exists(self.input_path):
                self.error.emit(f"Input file not found: {self.input_path}")
                return

            subtitle_path = os.path.join('temp', 'subtitle.srt')
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                for i, (start, end, text) in enumerate(self.subtitles, 1):
                    f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

            scale = {'9:16': '1080:1920', '16:9': '1920:1080', '1:1': '1080:1080'}[self.aspect_ratio]
            color = self.color.lstrip('#')
            color = f"&H{color[4:6]}{color[2:4]}{color[0:2]}"
            duration_map = {'Auto': '60', '<30s': '30', '30s - 60s': '60', '60s - 90s': '90', '90s - 3min': '180'}
            max_duration = duration_map.get(self.duration, '60')

            cmd = [
                'ffmpeg', '-i', self.input_path,
                '-vf', f"scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:(ow-iw)/2:(oh-ih)/2,subtitles='{subtitle_path}':force_style='FontName={self.font},PrimaryColour={color}'",
                '-t', max_duration, '-y', self.output_path
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                self.error.emit(f"FFmpeg error: {stderr}")
                return
            self.progress.emit(100)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(f"Unexpected error: {str(e)}")