import os
import urllib.request
from PyQt6.QtCore import QThread, pyqtSignal
from src.utils.youtube_downloader import get_thumbnail_url

class ThumbnailThread(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.thumbnail_path = os.path.join('temp', 'thumbnail.jpg')

    def run(self):
        try:
            thumbnail_url = get_thumbnail_url(self.url)
            if not thumbnail_url:
                self.progress.emit("Failed to fetch thumbnail URL")
                return

            os.makedirs(os.path.dirname(self.thumbnail_path), exist_ok=True)
            urllib.request.urlretrieve(thumbnail_url, self.thumbnail_path)
            self.finished.emit(self.thumbnail_path)
        except Exception as e:
            self.progress.emit(f"Error loading thumbnail: {str(e)}")