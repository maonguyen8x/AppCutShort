import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QComboBox, QPushButton, QFileDialog, QMessageBox, QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal
from src.processing.export_thread import ExportThread
from src.processing.process_thread import ProcessThread
from src.utils.youtube_downloader import download_youtube_video

# Thread for downloading YouTube video with progress
class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            output_path = os.path.join('temp', 'downloaded_video.mp4')
            ydl_opts = {
                'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                'outtmpl': output_path,
                'merge_output_format': 'mp4',
                'progress_hooks': [self.progress_hook],
            }
            from yt_dlp import YoutubeDL
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            if os.path.exists(output_path):
                self.finished.emit(output_path)
            else:
                self.error.emit("Failed to download video")
        except Exception as e:
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
        self.current_step = 0  # Track the current step (download, process, export)
        self.total_steps = 3  # Total steps: download, process, export
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # File name input
        filename_layout = QHBoxLayout()
        filename_label = QLabel("Name")
        filename_label.setStyleSheet("font-weight: bold;")
        self.filename_input = QLineEdit("0402")
        self.filename_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        filename_layout.addWidget(filename_label)
        filename_layout.addWidget(self.filename_input)
        layout.addLayout(filename_layout)

        # Export path
        path_layout = QHBoxLayout()
        path_label = QLabel("Export to Path")
        path_label.setStyleSheet("font-weight: bold;")
        self.path_input = QLineEdit()
        self.path_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.path_input.setReadOnly(True)
        path_btn = QPushButton("Browse")
        path_btn.setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
        path_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(path_btn)
        layout.addLayout(path_layout)

        # Video export options with checkbox
        self.video_checkbox = QCheckBox("Video")
        self.video_checkbox.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.video_checkbox.stateChanged.connect(self.toggle_video_options)
        layout.addWidget(self.video_checkbox)

        # Video options (resolution and frame rate)
        self.video_options_layout = QVBoxLayout()

        # Resolution selection
        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("Resolution")
        resolution_label.setStyleSheet("font-weight: bold;")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(['480p', '720p', '1080p', '2K', '4K'])
        self.resolution_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.resolution_combo.setEnabled(False)
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        self.video_options_layout.addLayout(resolution_layout)

        # Frame rate selection
        fps_layout = QHBoxLayout()
        fps_label = QLabel("Frame Rate")
        fps_label.setStyleSheet("font-weight: bold;")
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(['24fps', '25fps', '30fps', '50fps', '60fps'])
        self.fps_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.fps_combo.setEnabled(False)
        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(self.fps_combo)
        self.video_options_layout.addLayout(fps_layout)

        layout.addLayout(self.video_options_layout)

        # Progress label
        self.progress_label = QLabel("Progress: 0%")
        self.progress_label.setStyleSheet("color: #3b82f6; font-weight: bold; margin-top: 10px;")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        # Buttons
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("background-color: #3b82f6; padding: 10px; border-radius: 5px; margin-top: 10px;")
        export_btn.clicked.connect(self.export_video)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #ef4444; padding: 10px; border-radius: 5px; margin-top: 10px;")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def toggle_video_options(self, state):
        # Enable/disable video options based on checkbox state
        enabled = state == Qt.CheckState.Checked.value
        self.resolution_combo.setEnabled(enabled)
        self.fps_combo.setEnabled(enabled)

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Export Path")
        if path:
            self.path_input.setText(path)

    def update_progress(self, value):
        # Calculate overall progress based on the current step
        step_progress = (self.current_step / self.total_steps) * 100
        sub_progress = (value / self.total_steps)
        total_progress = int(step_progress + sub_progress)
        self.progress_label.setText(f"Progress: {total_progress}%")
        self.parent.progress_bar.setValue(total_progress)

    def export_video(self):
        # Validate inputs
        if not self.video_checkbox.isChecked():
            QMessageBox.warning(self, "Error", "Please check the 'Video' option to export.")
            return

        filename = self.filename_input.text()
        path = self.path_input.text()
        if not filename or not path:
            QMessageBox.warning(self, "Error", "Please provide a file name and export path")
            return

        output_path = os.path.join(path, f"{filename}.mp4")
        resolution = self.resolution_combo.currentText()
        fps = self.fps_combo.currentText().replace('fps', '')

        # Show progress bar and label
        self.progress_label.setVisible(True)
        self.parent.progress_bar.setVisible(True)
        self.parent.progress_bar.setValue(0)
        self.parent.status_label.setText("Downloading video...")

        # Step 1: Download the video
        self.current_step = 0
        url = self.parent.url_input.text()
        self.download_thread = DownloadThread(url)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(lambda path: self.on_download_finished(path, output_path, resolution, fps))
        self.download_thread.error.connect(self.parent.show_error)
        self.download_thread.start()

    def on_download_finished(self, downloaded_path, output_path, resolution, fps):
        # Update parent with the local video path
        self.parent.local_video_path = downloaded_path
        self.parent.status_label.setText("Processing video...")

        # Step 2: Process the video
        self.current_step = 1
        processed_path = os.path.join('temp', 'processed_video.mp4')
        self.process_thread = ProcessThread(
            self.parent.local_video_path, processed_path, self.parent.current_ratio,
            self.parent.current_font, self.parent.current_color, self.parent.subtitles,
            self.parent.current_language, self.parent.current_duration,
            font_size=self.parent.current_font_size, template=self.parent.current_template,
            caption_effect=self.parent.current_caption_effect,
            volume=self.parent.current_volume, audio_effect=self.parent.current_audio_effect,
            background_music=self.parent.current_background_music,
            color_filter=self.parent.current_color_filter,
            icons=self.parent.icons
        )
        self.process_thread.progress.connect(self.update_progress)
        self.process_thread.finished.connect(lambda path: self.on_process_finished(path, output_path, resolution, fps))
        self.process_thread.error.connect(self.parent.show_error)
        self.process_thread.start()

    def on_process_finished(self, processed_path, output_path, resolution, fps):
        self.parent.processed_path = processed_path
        self.parent.status_label.setText("Exporting video...")

        # Step 3: Export the video
        self.current_step = 2
        self.export_thread = ExportThread(processed_path, output_path, resolution, fps)
        self.export_thread.progress.connect(self.update_progress)
        self.export_thread.finished.connect(lambda path: self.parent.export_finished(path, self))
        self.export_thread.error.connect(self.parent.show_error)
        self.export_thread.start()