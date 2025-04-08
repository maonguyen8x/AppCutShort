import os
import sys
import logging
import re  # Thêm import re để sử dụng biểu thức chính quy
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
                             QLineEdit, QPushButton, QFrame, QFileDialog, QMessageBox, QProgressBar,
                             QDialog, QFormLayout, QToolBar)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QPixmap, QMovie, QDragEnterEvent, QDropEvent
from src.ui.edit_screen import EditScreen
from src.ui.export_dialog import ExportDialog
from src.utils.youtube_downloader import get_thumbnail_url
from src.utils.thumbnail_thread import ThumbnailThread

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='appcutshort.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

class LicenseKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter License Key")
        self.setStyleSheet("background-color: #3d3d3d; color: white;")
        self.setFixedSize(300, 150)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)
        self.key_input = QLineEdit()
        self.key_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px;")
        layout.addRow("License Key:", self.key_input)

        button_layout = QHBoxLayout()
        activate_btn = QPushButton("Activate")
        activate_btn.setStyleSheet("background-color: #3b82f6; padding: 5px 10px; border-radius: 5px; font-size: 14px;")
        activate_btn.clicked.connect(self.activate_key)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #ef4444; padding: 5px 10px; border-radius: 5px; font-size: 14px;")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(activate_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)

    def activate_key(self):
        key = self.key_input.text().strip()
        if key:
            # Placeholder for license key validation
            QMessageBox.information(self, "Success", "License key activated successfully!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Please enter a valid license key.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AppCutShort")
        self.setStyleSheet("background-color: #2d2d2d; color: white;")
        self.setMinimumSize(800, 600)
        self.is_licensed = False  # Simulate license status
        self.trial_videos_processed = 0
        self.trial_limit = 3
        self.local_video_path = None
        self.processed_path = None
        self.current_ratio = "16:9"
        self.current_duration = "Auto"
        self.current_font = "Arial.ttf"  # Default font
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
        # Create toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Help button
        help_btn = QPushButton("Help")
        help_btn.setStyleSheet("background-color: #4d4d4d; padding: 5px 10px; border-radius: 5px; font-size: 14px;")
        help_btn.clicked.connect(lambda: QMessageBox.information(self, "Help", "Contact support at support@appcutshort.com"))
        toolbar.addWidget(help_btn)

        # About button
        about_btn = QPushButton("About")
        about_btn.setStyleSheet("background-color: #4d4d4d; padding: 5px 10px; border-radius: 5px; font-size: 14px;")
        about_btn.clicked.connect(lambda: QMessageBox.information(self, "About", "AppCutShort v1.0\nDeveloped by xAI"))
        toolbar.addWidget(about_btn)

        # License button
        license_btn = QPushButton("License")
        license_btn.setStyleSheet("background-color: #4d4d4d; padding: 5px 10px; border-radius: 5px; font-size: 14px;")
        license_btn.clicked.connect(self.show_license_dialog)
        toolbar.addWidget(license_btn)

    def init_ui(self):
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Stacked widget to switch between screens
        self.screens = QWidget()
        self.screens_layout = QVBoxLayout(self.screens)
        self.layout.addWidget(self.screens)

        # Initial screen (URL input and drag-and-drop)
        self.initial_screen = QWidget()
        self.init_initial_screen()
        self.screens_layout.addWidget(self.initial_screen)

        # Edit screen
        self.edit_screen = EditScreen(self)
        self.screens_layout.addWidget(self.edit_screen)
        self.edit_screen.setVisible(False)

        # Status label
        self.status_label = QLabel("Please enter a YouTube URL")
        self.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { background-color: #4d4d4d; border-radius: 5px; } QProgressBar::chunk { background-color: #3b82f6; border-radius: 5px; }")
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

        # Enable drag-and-drop
        self.setAcceptDrops(True)

    def init_initial_screen(self):
        layout = QVBoxLayout(self.initial_screen)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Ensure the main layout is centered
        layout.setSpacing(15)

        # Use a single QHBoxLayout to place "YouTube URL" label, URL input, and "Continue" button
        input_row = QHBoxLayout()
        input_row.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the row
        input_row.setSpacing(2)  # Reduce spacing between elements

        # "YouTube URL" label
        url_label = QLabel("YouTube URL")
        url_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-right: 0px;")  # No margin to bring label closer

        # URL input field
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.setStyleSheet("background-color: #4d4d4d; padding: 8px; border: none; font-size: 14px; border-radius: 5px;")
        self.url_input.setMinimumWidth(600)  # Increase width to make input longer
        self.url_input.textChanged.connect(self.load_thumbnail)

        # Continue button (placed to the right of the URL input)
        self.continue_btn = QPushButton("Continue")
        self.continue_btn.setStyleSheet("background-color: #3b82f6; padding: 8px 20px; border-radius: 5px; font-size: 14px;")  # Blue color
        self.continue_btn.clicked.connect(self.switch_to_edit_screen)
        self.continue_btn.setFixedWidth(100)  # Set button width
        self.continue_btn.setVisible(False)  # Initially hidden

        # Add "YouTube URL" label, URL input, and "Continue" button to the row
        input_row.addWidget(url_label)
        input_row.addWidget(self.url_input)
        input_row.addWidget(self.continue_btn)

        # Loading animation label (placed below the URL input)
        self.button_loading_label = QLabel()
        self.button_loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.button_loading_label.setVisible(False)  # Initially hidden

        # Add the input row to the main layout
        layout.addLayout(input_row)
        layout.addWidget(self.button_loading_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.drop_area = QFrame()
        self.drop_area.setFixedSize(400, 150)
        self.drop_area.setStyleSheet("border: 2px dashed #3b82f6; border-radius: 10px; background-color: #3d3d3d;")
        self.drop_layout = QVBoxLayout(self.drop_area)
        self.drop_label = QLabel("Drag and Drop Video Here")
        self.drop_label.setStyleSheet("color: #aaaaaa; font-size: 16px;")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_layout.addWidget(self.drop_label)
        # Label to display dropped video info
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
        # Biểu thức chính quy để kiểm tra YouTube URL
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

        # Kiểm tra URL bằng biểu thức chính quy
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

        self.thumbnail_label.setText("")
        self.loading_movie = QMovie("loading.gif")
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
        self.initial_screen.setVisible(False)
        self.edit_screen.setVisible(True)
        self.status_label.setText("Edit your video")
        self.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")

    def show_export_dialog(self):
        dialog = ExportDialog(self)
        dialog.exec()

    def show_license_dialog(self):
        dialog = LicenseKeyDialog(self)
        if dialog.exec():
            self.is_licensed = True  # Simulate license activation

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())