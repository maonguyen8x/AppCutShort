import os
import logging
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QPushButton, QFileDialog, QMessageBox, QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from src.processing.export_thread import ExportThread
from src.processing.process_thread import ProcessThread
from src.utils.youtube_downloader import download_youtube_video
from src.ui.pro_dialog import ProDialog

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='appcutshort.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            logging.info(f"Starting video download for URL: {self.url}")
            output_path = os.path.join('temp', 'downloaded_video.mp4')
            os.makedirs('temp', exist_ok=True)

            success = download_youtube_video(self.url, output_path)

            if success:
                self.finished.emit(output_path)
            else:
                self.error.emit("Failed to download video: File not found")
        except Exception as e:
            logging.error(f"Error downloading video: {str(e)}")
            self.error.emit(f"Error downloading video: {str(e)}")

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded_bytes = d.get('downloaded_bytes')
            if total_bytes and downloaded_bytes:
                percent = int((downloaded_bytes / total_bytes) * 100)
                self.progress.emit(min(percent, 100))

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Export")
        self.setStyleSheet("background-color: #3d3d3d; color: white;")
        self.setMinimumSize(500, 350)
        self.current_step = 0
        self.total_steps = 3
        self.selected_resolution = "720p"  # Default value to avoid None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # File name input
        filename_layout = QHBoxLayout()
        filename_label = QLabel("Name")
        filename_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.filename_input = QLineEdit("0402")
        self.filename_input.setStyleSheet("background-color: #4d4d4d; padding: 8px; border-radius: 5px; font-size: 14px;")
        filename_layout.addWidget(filename_label)
        filename_layout.addWidget(self.filename_input)
        layout.addLayout(filename_layout)

        # Export path
        path_layout = QHBoxLayout()
        path_label = QLabel("Export to Path")
        path_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.path_input = QLineEdit()
        self.path_input.setStyleSheet("background-color: #4d4d4d; padding: 8px; border-radius: 5px; font-size: 14px;")
        self.path_input.setReadOnly(True)
        path_btn = QPushButton("Browse")
        path_btn.setStyleSheet("background-color: #3b82f6; padding: 8px 15px; border-radius: 5px; font-size: 14px;")
        path_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(path_btn)
        layout.addLayout(path_layout)

        # Video export options with checkbox
        self.video_checkbox = QCheckBox("Video")
        self.video_checkbox.setStyleSheet("font-weight: bold; margin-top: 10px; font-size: 14px;")
        self.video_checkbox.setChecked(False)
        self.video_checkbox.stateChanged.connect(self.toggle_video_options)
        layout.addWidget(self.video_checkbox)

        # Video options (resolution and frame rate)
        self.video_options_layout = QVBoxLayout()

        # Resolution selection
        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("Resolution")
        resolution_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(['480p', '720p', '1080p (Pro)', '2K (Pro)', '4K (Pro)'])
        self.resolution_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px; opacity: 0.5;")
        self.resolution_combo.setEnabled(False)
        self.resolution_combo.currentTextChanged.connect(self.check_resolution_selection)
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        self.video_options_layout.addLayout(resolution_layout)

        # Frame rate selection
        fps_layout = QHBoxLayout()
        fps_label = QLabel("Frame Rate")
        fps_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(['24fps', '25fps', '30fps', '50fps', '60fps'])
        self.fps_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px; opacity: 0.5;")
        self.fps_combo.setEnabled(False)
        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(self.fps_combo)
        self.video_options_layout.addLayout(fps_layout)

        layout.addLayout(self.video_options_layout)

        # Progress label
        self.progress_label = QLabel("Progress: 0%")
        self.progress_label.setStyleSheet("color: #3b82f6; font-weight: bold; margin-top: 10px; font-size: 14px;")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # Buttons
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("background-color: #3b82f6; padding: 10px 20px; border-radius: 5px; margin-top: 10px; font-size: 14px;")
        export_btn.clicked.connect(self.export_video)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #ef4444; padding: 10px 20px; border-radius: 5px; margin-top: 10px; font-size: 14px;")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def toggle_video_options(self, state):
        enabled = state == Qt.CheckState.Checked.value
        self.resolution_combo.setEnabled(enabled)
        self.fps_combo.setEnabled(enabled)
        if enabled:
            self.resolution_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px; opacity: 1.0;")
            self.fps_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px; opacity: 1.0;")
        else:
            self.resolution_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px; opacity: 0.5;")
            self.fps_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px; opacity: 0.5;")

    def check_resolution_selection(self, resolution):
        self.selected_resolution = resolution
        if not self.parent.is_licensed and '(Pro)' in resolution:
            pro_dialog = ProDialog(self)
            pro_dialog.exec()
            self.resolution_combo.setCurrentText('720p')
            self.selected_resolution = '720p'  # Ensure selected_resolution is updated

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Export Path")
        if path:
            self.path_input.setText(path)

    def update_progress(self, value):
        step_progress = (self.current_step / self.total_steps) * 100
        sub_progress = (value / self.total_steps)
        total_progress = int(step_progress + sub_progress)
        self.progress_label.setText(f"Progress: {total_progress}%")
        self.parent.progress_bar.setValue(total_progress)

    def export_video(self):
        if not self.video_checkbox.isChecked():
            QMessageBox.warning(self, "Error", "Please check the 'Video' option to export.")
            return

        filename = self.filename_input.text()
        path = self.path_input.text()
        if not filename or not path:
            QMessageBox.warning(self, "Error", "Please provide a file name and export path")
            return

        if not os.path.isdir(path):
            QMessageBox.critical(self, "Error", f"Export path does not exist or is not a directory: {path}")
            logging.error(f"Export path does not exist or is not a directory: {path}")
            return
        if not os.access(path, os.W_OK):
            QMessageBox.critical(self, "Error", f"Export path is not writable: {path}")
            logging.error(f"Export path is not writable: {path}")
            return

        output_path = os.path.join(path, f"{filename}.mp4")
        resolution = self.selected_resolution if self.selected_resolution else "720p"  # Fallback to 720p
        resolution = resolution.replace(' (Pro)', '')  # Remove "(Pro)" for FFmpeg command
        fps = self.fps_combo.currentText().replace('fps', '')

        logging.info(f"Starting export process. Output path: {output_path}, Resolution: {resolution}, FPS: {fps}")

        self.progress_label.setVisible(True)
        self.parent.progress_bar.setVisible(True)
        self.parent.progress_bar.setValue(0)
        self.parent.status_label.setText("Downloading video...")

        self.current_step = 0
        url = self.parent.url_input.text()
        if not url:
            QMessageBox.critical(self, "Error", "No YouTube URL provided")
            logging.error("No YouTube URL provided for download")
            self.parent.show_error("No YouTube URL provided")
            return

        logging.info(f"Downloading video from URL: {url}")
        self.download_thread = DownloadThread(url)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(lambda path: self.on_download_finished(path, output_path, resolution, fps))
        self.download_thread.error.connect(self.on_download_error)
        self.download_thread.start()

    def on_download_error(self, error_message):
        logging.error(f"Download failed: {error_message}")
        self.parent.show_error(error_message)
        self.progress_label.setVisible(False)
        self.parent.progress_bar.setVisible(False)

    def on_download_finished(self, downloaded_path, output_path, resolution, fps):
        logging.info(f"Download completed. Downloaded path: {downloaded_path}")
        if not os.path.exists(downloaded_path):
            error_message = f"Downloaded video file not found: {downloaded_path}"
            logging.error(error_message)
            self.parent.show_error(error_message)
            self.progress_label.setVisible(False)
            self.parent.progress_bar.setVisible(False)
            return

        self.parent.local_video_path = downloaded_path
        self.parent.status_label.setText("Processing video...")

        self.current_step = 1
        processed_path = os.path.join('temp', 'processed_video.mp4')
        logging.info(f"Starting video processing. Input: {downloaded_path}, Output: {processed_path}")
        self.process_thread = ProcessThread(
            self.parent.local_video_path,
            processed_path,
            self.parent.subtitles,
            self.parent.current_ratio,
            self.parent.current_duration,
            self.parent.current_font,
            self.parent.current_font_size,
            self.parent.current_color,
            self.parent.current_template,
            self.parent.current_volume,
            self.parent.current_audio_effect,
            self.parent.current_background_music,
            self.parent.current_caption_effect,
            self.parent.current_color_filter,
            resolution,
            fps
        )
        self.process_thread.progress.connect(self.update_progress)
        self.process_thread.finished.connect(lambda path: self.on_process_finished(path, output_path, resolution, fps))
        self.process_thread.error.connect(self.on_process_error)
        self.process_thread.start()

    def on_process_error(self, error_message):
        logging.error(f"Processing failed: {error_message}")
        self.parent.show_error(error_message)
        self.progress_label.setVisible(False)
        self.parent.progress_bar.setVisible(False)

    def on_process_finished(self, processed_path, output_path, resolution, fps):
        logging.info(f"Processing completed. Processed path: {processed_path}")
        if not os.path.exists(processed_path):
            error_message = f"Processed video file not found: {processed_path}"
            logging.error(error_message)
            self.parent.show_error(error_message)
            self.progress_label.setVisible(False)
            self.parent.progress_bar.setVisible(False)
            return

        self.parent.processed_path = processed_path
        self.parent.status_label.setText("Exporting video...")

        self.current_step = 2
        logging.info(f"Starting final export. Input: {processed_path}, Output: {output_path}, Resolution: {resolution}, FPS: {fps}")
        self.export_thread = ExportThread(processed_path, output_path, resolution, fps)
        self.export_thread.progress.connect(self.update_progress)
        self.export_thread.finished.connect(lambda path: self.on_export_finished(path))
        self.export_thread.error.connect(self.on_export_error)
        self.export_thread.start()

    def on_export_error(self, error_message):
        logging.error(f"Export failed: {error_message}")
        self.parent.show_error(error_message)
        self.progress_label.setVisible(False)
        self.parent.progress_bar.setVisible(False)

    def on_export_finished(self, output_path):
        logging.info(f"Export completed successfully. Output path: {output_path}")
        self.parent.export_finished(output_path, self)
        self.progress_label.setVisible(False)
        self.parent.progress_bar.setVisible(False)