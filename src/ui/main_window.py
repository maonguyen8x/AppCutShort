import os
import sys
import logging
import re
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
                             QLineEdit, QPushButton, QFrame, QFileDialog, QMessageBox,
                             QDialog, QFormLayout, QToolBar)
from PyQt6.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QMovie, QDragEnterEvent, QDropEvent
from src.ui.edit_screen import EditScreen
from src.ui.export_dialog import ExportDialog
from src.ui.license_dialog import LicenseKeyDialog
from src.utils.youtube_downloader import get_thumbnail_url, check_video_availability, download_youtube_video
from src.utils.thumbnail_thread import ThumbnailThread

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='appcutshort.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DownloadThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, output_path):
        super().__init__()
        self.url = url
        self.output_path = output_path

    def run(self):
        try:
            logging.info(f"Starting video download for URL: {self.url}")
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

            success, error_message = download_youtube_video(self.url, self.output_path)
            if success:
                # Convert video to H.264 if necessary
                converted_path = self.output_path.replace('.mp4', '_converted.mp4')
                try:
                    subprocess.run([
                        'ffmpeg', '-i', self.output_path, '-c:v', 'libx264', '-c:a', 'aac', '-y', converted_path
                    ], check=True, capture_output=True, text=True)
                    if os.path.exists(converted_path):
                        os.remove(self.output_path)
                        os.rename(converted_path, self.output_path)
                        logging.info(f"Video converted to H.264: {self.output_path}")
                    else:
                        logging.error("Converted video file not found after FFmpeg conversion")
                        self.error.emit("Converted video file not found after FFmpeg conversion")
                        return
                except subprocess.CalledProcessError as e:
                    logging.error(f"FFmpeg conversion failed: {str(e)}")
                    self.error.emit(f"FFmpeg conversion failed: {str(e.stderr)}")
                    return
                self.finished.emit(self.output_path)
            else:
                self.error.emit(error_message or "Downloaded video file not found")
        except Exception as e:
            logging.error(f"Error downloading video: {str(e)}")
            self.error.emit(f"Error downloading video: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AppCutShort - Video Editor")
        self.setStyleSheet("background-color: #1a1a1a; color: white;")
        self.setMinimumSize(1200, 800)
        self.is_licensed = False
        self.trial_videos_processed = 0
        self.trial_limit = 3
        self.local_video_path = None
        self.current_video_url = None
        self.thumbnail_path = None
        self.current_ratio = "16:9"
        self.current_duration = "Auto"
        self.current_font = "Arial.ttf"
        self.current_font_size = 24
        self.current_color = "white"
        self.current_template = "Default"
        self.current_caption_effect = "None"
        self.current_volume = 1.0
        self.current_audio_effect = "None"
        self.current_background_music = None
        self.current_color_filter = "None"
        self.subtitles = []
        self.current_language = "en"
        self.icons = []
        self.thumbnail_loaded = False
        self.init_ui()
        self.init_toolbar()

    def init_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        new_project_btn = QPushButton("New Project")
        new_project_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        new_project_btn.clicked.connect(self.new_project)
        toolbar.addWidget(new_project_btn)

        help_btn = QPushButton("Help")
        help_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        help_btn.clicked.connect(lambda: QMessageBox.information(self, "Help", "Contact support at support@appcutshort.com"))
        toolbar.addWidget(help_btn)

        about_btn = QPushButton("About")
        about_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        about_btn.clicked.connect(lambda: QMessageBox.information(self, "About", "AppCutShort v1.0\nDeveloped by xAI"))
        toolbar.addWidget(about_btn)

        license_btn = QPushButton("License")
        license_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        license_btn.clicked.connect(self.show_license_dialog)
        toolbar.addWidget(license_btn)

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.screens = QWidget()
        self.screens_layout = QVBoxLayout(self.screens)
        self.layout.addWidget(self.screens)

        self.initial_screen = QWidget()
        self.init_initial_screen()
        self.screens_layout.addWidget(self.initial_screen)

        self.edit_screen = EditScreen(self)
        self.screens_layout.addWidget(self.edit_screen)
        self.edit_screen.setVisible(False)

        self.status_label = QLabel("Please enter a YouTube URL or drop a video file")
        self.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        self.setAcceptDrops(True)

    def init_initial_screen(self):
        layout = QVBoxLayout(self.initial_screen)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        input_row = QHBoxLayout()
        input_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_row.setSpacing(5)

        url_label = QLabel("YouTube URL")
        url_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-right: 0px;")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.setStyleSheet("background-color: #3d3d3d; padding: 8px; border: none; font-size: 14px; border-radius: 5px; color: white;")
        self.url_input.setMinimumWidth(600)
        self.url_input.textChanged.connect(self.load_thumbnail)

        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setStyleSheet("background-color: #3b82f6; padding: 8px 20px; border-radius: 5px; font-size: 14px;")
        self.continue_btn.clicked.connect(self.switch_to_edit_screen)
        self.continue_btn.setFixedWidth(100)
        self.continue_btn.setVisible(False)

        input_row.addWidget(url_label)
        input_row.addWidget(self.url_input)
        input_row.addWidget(self.continue_btn)

        self.button_loading_label = QLabel()
        self.button_loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button_loading_label.setVisible(False)

        layout.addLayout(input_row)
        layout.addWidget(self.button_loading_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.drop_area = QFrame()
        self.drop_area.setFixedSize(400, 150)
        self.drop_area.setStyleSheet("border: 2px dashed #3b82f6; border-radius: 10px; background-color: #2d2d2d;")
        self.drop_layout = QVBoxLayout(self.drop_area)
        self.drop_label = QLabel("Drag and Drop Video Here")
        self.drop_label.setStyleSheet("color: #aaaaaa; font-size: 16px;")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_layout.addWidget(self.drop_label)
        self.dropped_video_label = QLabel("")
        self.dropped_video_label.setStyleSheet("color: white; font-size: 14px;")
        self.dropped_video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dropped_video_label.setWordWrap(True)
        self.dropped_video_label.setVisible(False)
        self.drop_layout.addWidget(self.dropped_video_label)
        layout.addWidget(self.drop_area, alignment=Qt.AlignmentFlag.AlignCenter)

        self.thumbnail_label = QLabel("No thumbnail loaded")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("color: gray; margin: 20px; font-size: 14px;")
        layout.addWidget(self.thumbnail_label)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if self.enforce_trial_restrictions():
            return

        files = [url.toLocalFile() for url in event.mimeData().urls()]
        if files:
            file_path = files[0]
            if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                self.local_video_path = file_path
                self.dropped_video_label.setText(os.path.basename(file_path))
                self.dropped_video_label.setVisible(True)
                self.drop_label.setVisible(False)
                self.status_label.setText("Video loaded successfully")
                self.status_label.setStyleSheet("font-size: 14px; color: #3b82f6;")
                self.switch_to_edit_screen()
            else:
                self.status_label.setText("Please drop a valid video file (mp4, mov, avi, mkv)")
                self.status_label.setStyleSheet("font-size: 14px; color: #ef4444;")

    def enforce_trial_restrictions(self):
        if not self.is_licensed and self.trial_videos_processed >= self.trial_limit:
            QMessageBox.warning(self, "Trial Limit Reached", "You have reached the trial limit of 3 videos. Please upgrade to continue.")
            return True
        return False

    def validate_youtube_url(self, url):
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube\.com/watch\?v=|youtu\.be/)'
            r'[\w-]{11}'
        )
        return re.match(youtube_regex, url) is not None

    def load_thumbnail(self, url):
        if self.enforce_trial_restrictions():
            return

        self.thumbnail_loaded = False

        if not url:
            self.continue_btn.setVisible(False)
            self.button_loading_label.setVisible(False)
            self.thumbnail_label.setText("No thumbnail loaded")
            self.thumbnail_label.setStyleSheet("color: gray; margin: 20px; font-size: 14px;")
            self.thumbnail_label.setVisible(True)
            self.status_label.setText("Please enter a YouTube URL")
            self.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")
            return

        if not self.validate_youtube_url(url):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid YouTube URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID or https://youtu.be/VIDEO_ID)")
            self.continue_btn.setVisible(False)
            self.button_loading_label.setVisible(False)
            self.thumbnail_label.setText("Please enter a valid YouTube URL")
            self.thumbnail_label.setStyleSheet("color: #ef4444; margin: 20px; font-size: 14px;")
            self.thumbnail_label.setVisible(True)
            self.status_label.setText("Invalid YouTube URL")
            self.status_label.setStyleSheet("font-size: 14px; color: #ef4444;")
            return

        is_available, error_message = check_video_availability(url)
        if not is_available:
            QMessageBox.warning(self, "Video Unavailable", f"Cannot load video: {error_message}")
            self.continue_btn.setVisible(False)
            self.button_loading_label.setVisible(False)
            self.thumbnail_label.setText("Video unavailable")
            self.thumbnail_label.setStyleSheet("color: #ef4444; margin: 20px; font-size: 14px;")
            self.thumbnail_label.setVisible(True)
            self.status_label.setText("Video unavailable")
            self.status_label.setStyleSheet("font-size: 14px; color: #ef4444;")
            return

        self.thumbnail_label.setText("")
        self.loading_movie = QMovie("resources/loading.gif")
        if not self.loading_movie.isValid():
            logging.warning("Loading GIF not found or invalid. Falling back to text.")
            self.thumbnail_label.setText("Loading thumbnail...")
        else:
            self.thumbnail_label.setMovie(self.loading_movie)
            self.loading_movie.start()
        self.thumbnail_label.setStyleSheet("margin: 20px;")
        self.thumbnail_label.setVisible(True)

        self.button_loading_label.setVisible(False)

        self.status_label.setText("Loading thumbnail...")
        self.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")

        self.thumbnail_thread = ThumbnailThread(url)
        self.thumbnail_thread.finished.connect(self.on_thumbnail_loaded)
        self.thumbnail_thread.progress.connect(self.status_label.setText)
        self.thumbnail_thread.start()

    def on_thumbnail_loaded(self, thumbnail_path):
        if os.path.exists(thumbnail_path):
            pixmap = QPixmap(thumbnail_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(320, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.thumbnail_label.setPixmap(scaled_pixmap)
                self.thumbnail_label.setStyleSheet("margin: 20px;")
                self.status_label.setText("Thumbnail loaded successfully")
                self.status_label.setStyleSheet("font-size: 14px; color: #3b82f6;")
                self.continue_btn.setVisible(True)
                self.thumbnail_loaded = True
                self.thumbnail_path = thumbnail_path
            else:
                self.thumbnail_label.setText("Failed to load thumbnail")
                self.thumbnail_label.setStyleSheet("color: #ef4444; margin: 20px; font-size: 14px;")
                self.status_label.setText("Failed to load thumbnail")
                self.status_label.setStyleSheet("font-size: 14px; color: #ef4444;")
        else:
            self.thumbnail_label.setText("Failed to load thumbnail")
            self.thumbnail_label.setStyleSheet("color: #ef4444; margin: 20px; font-size: 14px;")
            self.status_label.setText("Failed to load thumbnail")
            self.status_label.setStyleSheet("font-size: 14px; color: #ef4444;")

        if hasattr(self, 'loading_movie'):
            self.loading_movie.stop()

    def switch_to_edit_screen(self):
        if not self.local_video_path and not self.url_input.text():
            QMessageBox.warning(self, "Error", "Please provide a video URL or drop a video file.")
            return

        if self.url_input.text() and not self.local_video_path:
            self.current_video_url = self.url_input.text()
            # Download video temporarily for preview
            temp_path = os.path.join('temp', 'preview_video.mp4')
            self.download_thread = DownloadThread(self.current_video_url, temp_path)
            self.download_thread.finished.connect(self.on_download_finished_for_preview)
            self.download_thread.error.connect(self.on_download_error)
            self.download_thread.start()
            self.status_label.setText("Downloading video for preview...")
            self.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")
        else:
            self.local_video_path = self.local_video_path
            self.initial_screen.setVisible(False)
            self.edit_screen.setVisible(True)
            self.edit_screen.load_video(self.local_video_path)
            self.status_label.setText("Edit your video")
            self.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")

    def on_download_finished_for_preview(self, downloaded_path):
        self.local_video_path = downloaded_path
        self.initial_screen.setVisible(False)
        self.edit_screen.setVisible(True)
        self.edit_screen.load_video(self.local_video_path)
        self.status_label.setText("Edit your video")
        self.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")

    def show_export_dialog(self):
        dialog = ExportDialog(self)
        if dialog.exec():
            output_path = dialog.output_path.text()
            if not output_path:
                QMessageBox.warning(self, "Error", "Please specify an output path.")
                return

            resolution = dialog.resolution_combo.currentText()
            if resolution in ["1080p", "2K", "4K"] and not self.is_licensed:
                QMessageBox.warning(self, "Pro Feature", "Please upgrade to Pro to export in 1080p, 2K, or 4K.")
                return

            self.status_label.setText("Exporting video...")
            self.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")

            # Prepare parameters for video export
            from src.utils.video_processor import process_video
            temp_output = os.path.join('temp', 'temp_output.mp4')
            aspect_ratio = self.current_ratio
            resolution_map = {
                "480p": "854:480",
                "720p": "1280:720",
                "1080p": "1920:1080",
                "2K": "2560:1440",
                "4K": "3840:2160"
            }
            resolution = resolution_map[resolution]

            try:
                # Call C++ video processor
                success = process_video(
                    input_path=self.local_video_path,
                    output_path=temp_output,
                    resolution=resolution,
                    aspect_ratio=aspect_ratio,
                    background_music=self.current_background_music,
                    volume=self.current_volume,
                    font=self.current_font,
                    font_size=self.current_font_size,
                    text_color=self.current_color,
                    icons=self.icons
                )
                if success:
                    import shutil
                    shutil.move(temp_output, output_path)
                    self.export_finished(output_path, dialog)
                else:
                    self.show_error("Failed to process video. Check logs for details.")
            except Exception as e:
                self.show_error(f"Error exporting video: {str(e)}")

    def on_download_error(self, error_message):
        self.status_label.setText(f"Failed to download video: {error_message}")
        self.status_label.setStyleSheet("font-size: 14px; color: #ef4444;")
        QMessageBox.critical(self, "Download Error", error_message)

    def show_license_dialog(self):
        dialog = LicenseKeyDialog(self)
        if dialog.exec():
            self.is_licensed = True

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.status_label.setText("Error occurred")
        self.status_label.setStyleSheet("font-size: 14px; color: #ef4444;")

    def export_finished(self, output_path, dialog):
        if not self.is_licensed:
            self.trial_videos_processed += 1
        QMessageBox.information(self, "Export Complete", f"Video exported successfully to:\n{output_path}")
        self.status_label.setText("Export completed")
        self.status_label.setStyleSheet("font-size: 14px; color: #3b82f6;")
        dialog.accept()

    def new_project(self):
        self.initial_screen.setVisible(True)
        self.edit_screen.setVisible(False)
        self.local_video_path = None
        self.current_video_url = None
        self.thumbnail_path = None
        self.url_input.clear()
        self.status_label.setText("Please enter a YouTube URL or drop a video file")
        self.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")