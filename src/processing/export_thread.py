import subprocess
import re
from PyQt6.QtCore import QThread, pyqtSignal

class ExportThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, input_path, output_path, resolution):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.resolution = resolution

    def run(self):
        try:
            if self.resolution == '720p':
                scale = 'scale=1280:720'
            elif self.resolution == '1080p':
                scale = 'scale=1920:1080'
            elif self.resolution == '2K':
                scale = 'scale=2560:1440'
            else:
                scale = 'scale=3840:2160'

            cmd = [
                'ffmpeg', '-i', self.input_path,
                '-vf', scale,
                '-y', self.output_path
            ]

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            duration = None
            for line in process.stdout:
                if duration is None and 'Duration' in line:
                    match = re.search(r'Duration: (\d+):(\d+):(\d+.\d+)', line)
                    if match:
                        hours, minutes, seconds = map(float, match.groups())
                        duration = hours * 3600 + minutes * 60 + seconds
                if 'time=' in line and duration:
                    match = re.search(r'time=(\d+):(\d+):(\d+.\d+)', line)
                    if match:
                        hours, minutes, seconds = map(float, match.groups())
                        current_time = hours * 3600 + minutes * 60 + seconds
                        percent = int((current_time / duration) * 100)
                        self.progress.emit(min(percent, 100))

            process.wait()
            if process.returncode == 0:
                self.finished.emit(self.output_path)
            else:
                self.error.emit("Error exporting video")
        except Exception as e:
            self.error.emit(str(e))