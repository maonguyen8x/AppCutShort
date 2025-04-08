import os
import logging
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from src.utils.youtube_downloader import get_thumbnail_url

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='appcutshort.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

class ThumbnailThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.thumbnail_path = os.path.join('temp', 'thumbnail.jpg')

    def run(self):
        try:
            # Ensure temp directory exists
            os.makedirs('temp', exist_ok=True)

            # Get thumbnail URL
            self.progress.emit("Fetching thumbnail URL...")
            thumbnail_url = get_thumbnail_url(self.url)
            if not thumbnail_url:
                self.error.emit("Failed to fetch thumbnail URL")
                return

            # Download the thumbnail
            self.progress.emit("Downloading thumbnail...")
            response = requests.get(thumbnail_url, stream=True)
            if response.status_code != 200:
                self.error.emit("Failed to download thumbnail")
                return

            # Save the thumbnail to a file
            with open(self.thumbnail_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    if chunk:
                        f.write(chunk)

            if os.path.exists(self.thumbnail_path):
                self.finished.emit(self.thumbnail_path)
            else:
                self.error.emit("Thumbnail file not found after download")
        except Exception as e:
            logging.error(f"Error in ThumbnailThread: {str(e)}")
            self.error.emit(f"Error downloading thumbnail: {str(e)}")