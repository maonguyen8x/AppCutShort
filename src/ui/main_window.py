import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
                             QMessageBox, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFileDialog, QColorDialog)
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtGui import QPixmap
from src.ui.subtitle_dialog import SubtitleDialog
from src.ui.export_dialog import ExportDialog
from src.ui.license_dialog import LicenseDialog
from src.processing.process_thread import ProcessThread
from src.processing.ai_processor import generate_subtitles, translate_subtitles
from src.utils.youtube_downloader import download_youtube_video

TRIAL_DAYS = 7
TRIAL_START_FILE = "trial_start.txt"
LICENSE_FILE = "license.key"

class VideoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AppCutShort")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #2d2d2d; color: white;")
        self.video_path = None
        self.processed_path = None
        self.subtitles = []
        self.is_modified = False
        self.current_ratio = '16:9'
        self.current_language = 'English'
        self.current_duration = 'Auto'
        self.is_trial_active = self.check_trial_period()
        self.is_licensed = self.check_license()
        self.init_ui()
        self.setAcceptDrops(True)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        menu_bar = QHBoxLayout()
        title_label = QLabel("AppCutShort")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        import_btn = QPushButton("Import")
        import_btn.setStyleSheet("background-color: #3b82f6; padding: 5px 15px; border-radius: 5px;")
        import_btn.clicked.connect(self.import_video)
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("background-color: #22c55e; padding: 5px 15px; border-radius: 5px;")
        export_btn.clicked.connect(self.show_export_dialog)
        license_btn = QPushButton("Enter License")
        license_btn.setStyleSheet("background-color: #f59e0b; padding: 5px 15px; border-radius: 5px;")
        license_btn.clicked.connect(self.enter_license_key)
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #ef4444; padding: 5px 15px; border-radius: 5px;")
        close_btn.clicked.connect(self.close)
        menu_bar.addWidget(title_label)
        menu_bar.addStretch()
        menu_bar.addWidget(import_btn)
        menu_bar.addWidget(export_btn)
        menu_bar.addWidget(license_btn)
        menu_bar.addWidget(close_btn)
        main_layout.addLayout(menu_bar)

        content_layout = QHBoxLayout()
        self.preview_area = QFrame()
        self.preview_area.setStyleSheet("background-color: rgba(0, 0, 0, 0.7); border-radius: 10px;")
        self.preview_area.setFixedWidth(800)
        preview_layout = QVBoxLayout(self.preview_area)
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        preview_layout.addWidget(self.video_widget)
        self.preview_label = QLabel("No video loaded\nClick to browse or drag & drop video")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: gray;")
        self.preview_label.mousePressEvent = self.browse_video
        preview_layout.addWidget(self.preview_label)
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setVisible(False)
        preview_layout.addWidget(self.thumbnail_label)
        self.update_preview_size()
        content_layout.addWidget(self.preview_area)

        edit_panel = QFrame()
        edit_panel.setStyleSheet("background-color: #3d3d3d; border-radius: 10px; padding: 10px;")
        edit_layout = QVBoxLayout(edit_panel)

        url_label = QLabel("YouTube URL")
        url_label.setStyleSheet("font-weight: bold;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.url_input.textChanged.connect(self.load_thumbnail)
        upload_btn = QPushButton("Upload")
        upload_btn.setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
        upload_btn.clicked.connect(self.load_video)
        browse_btn = QPushButton("Browse Video\nDrag or Drop Video")
        browse_btn.setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
        browse_btn.clicked.connect(self.browse_video)
        edit_layout.addWidget(url_label)
        edit_layout.addWidget(self.url_input)
        edit_layout.addWidget(upload_btn)
        edit_layout.addWidget(browse_btn)

        ratio_label = QLabel("Aspect Ratio")
        ratio_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        ratio_layout = QHBoxLayout()
        self.ratio_buttons = {}
        for ratio in ['9:16', '16:9', '1:1']:
            btn = QPushButton(ratio)
            btn.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
            btn.clicked.connect(lambda checked, r=ratio: self.select_ratio(r))
            ratio_layout.addWidget(btn)
            self.ratio_buttons[ratio] = btn
        self.ratio_buttons['16:9'].setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
        edit_layout.addWidget(ratio_label)
        edit_layout.addLayout(ratio_layout)

        language_label = QLabel("Language")
        language_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.language_combo = QComboBox()
        self.language_combo.addItems(['English', 'Vietnamese', 'Japanese'])
        self.language_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.language_combo.currentTextChanged.connect(self.change_language)
        edit_layout.addWidget(language_label)
        edit_layout.addWidget(self.language_combo)

        duration_label = QLabel("Video Duration")
        duration_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(['Auto', '<30s', '30s - 60s', '60s - 90s', '90s - 3min'])
        self.duration_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.duration_combo.currentTextChanged.connect(self.change_duration)
        edit_layout.addWidget(duration_label)
        edit_layout.addWidget(self.duration_combo)

        font_label = QLabel("Font")
        font_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.font_combo = QComboBox()
        self.font_combo.addItems(['Arial', 'Times New Roman', 'Helvetica', 'Calibri', 'Roboto', 'Montserrat'])
        self.font_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        edit_layout.addWidget(font_label)
        edit_layout.addWidget(self.font_combo)

        color_label = QLabel("Caption Color")
        color_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.color_btn = QPushButton("Pick Color")
        self.color_btn.setStyleSheet("background-color: #ffffff; padding: 5px; border-radius: 5px;")
        self.color_btn.clicked.connect(self.pick_color)
        edit_layout.addWidget(color_label)
        edit_layout.addWidget(self.color_btn)

        continue_btn = QPushButton("Continue")
        continue_btn.setStyleSheet("background-color: #3b82f6; padding: 10px; border-radius: 5px; margin-top: 20px;")
        continue_btn.clicked.connect(self.process_video)
        edit_layout.addWidget(continue_btn)

        edit_layout.addStretch()
        content_layout.addWidget(edit_panel)
        main_layout.addLayout(content_layout)

        timeline_area = QFrame()
        timeline_area.setStyleSheet("background-color: #3d3d3d; border-radius: 10px;")
        timeline_area.setFixedHeight(150)
        timeline_layout = QVBoxLayout(timeline_area)
        self.subtitle_table = QTableWidget()
        self.subtitle_table.setStyleSheet("background-color: #4d4d4d; border: none;")
        self.subtitle_table.setColumnCount(3)
        self.subtitle_table.setHorizontalHeaderLabels(['Start', 'End', 'Text'])
        self.subtitle_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.subtitle_table.setRowCount(0)
        self.subtitle_table.itemChanged.connect(self.mark_modified)
        timeline_layout.addWidget(self.subtitle_table)
        main_layout.addWidget(timeline_area)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("margin-top: 10px;")
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel(self.get_status_text())
        self.status_label.setStyleSheet("font-size: 12px; color: #aaaaaa;")
        main_layout.addWidget(self.status_label)

    def load_thumbnail(self, url):
        if self.enforce_trial_restrictions():
            return
        if url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/"):
            thumbnail_path = download_youtube_video(url, thumbnail_only=True)
            if thumbnail_path:
                pixmap = QPixmap(thumbnail_path)
                self.thumbnail_label.setPixmap(pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio))
                self.thumbnail_label.setVisible(True)
                self.preview_label.setVisible(False)
            else:
                self.thumbnail_label.setVisible(False)
                self.preview_label.setVisible(True)

    def load_video(self):
        if self.enforce_trial_restrictions():
            return
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
            return
        self.video_path = download_youtube_video(url)
        if self.video_path:
            self.load_video_to_player(self.video_path)
            self.thumbnail_label.setVisible(False)
        else:
            QMessageBox.critical(self, "Error", "Failed to load video")

    def check_trial_period(self):
        if os.path.exists(TRIAL_START_FILE):
            with open(TRIAL_START_FILE, 'r') as f:
                start_date = datetime.strptime(f.read().strip(), "%Y-%m-%d")
            if datetime.now() <= start_date + timedelta(days=TRIAL_DAYS):
                return True
            return False
        else:
            with open(TRIAL_START_FILE, 'w') as f:
                f.write(datetime.now().strftime("%Y-%m-%d"))
            return True

    def check_license(self):
        if os.path.exists(LICENSE_FILE):
            with open(LICENSE_FILE, 'r') as f:
                key = f.read().strip()
            return key == "VALID_LICENSE_KEY"
        return False

    def get_status_text(self):
        if self.is_licensed:
            return "Licensed Version"
        elif self.is_trial_active:
            return f"Trial Version - {TRIAL_DAYS} days remaining"
        else:
            return "Trial Expired - Please purchase a license"

    def enforce_trial_restrictions(self):
        if not self.is_licensed and not self.is_trial_active:
            QMessageBox.critical(self, "Trial Expired", "Your trial has expired. Please purchase a license key.")
            return True
        return False

    def import_video(self):
        if self.enforce_trial_restrictions():
            return
        self.url_input.setFocus()

    def browse_video(self, event=None):
        if self.enforce_trial_restrictions():
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            self.video_path = file_path
            self.load_video_to_player(self.video_path)
            self.preview_label.hide()
            self.thumbnail_label.setVisible(False)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if self.enforce_trial_restrictions():
            return
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                self.video_path = file_path
                self.load_video_to_player(self.video_path)
                self.preview_label.hide()
                self.thumbnail_label.setVisible(False)

    def load_video_to_player(self, video_path):
        self.player.setSource(QUrl.fromLocalFile(video_path))
        self.player.play()
        self.update_preview_size()

    def select_ratio(self, ratio):
        if self.enforce_trial_restrictions():
            return
        self.current_ratio = ratio
        for r, btn in self.ratio_buttons.items():
            btn.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.ratio_buttons[ratio].setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
        self.update_preview_size()

    def update_preview_size(self):
        if self.current_ratio == '9:16':
            self.preview_area.setFixedWidth(400)
            self.preview_area.setFixedHeight(711)
            self.preview_area.setStyleSheet("background-color: rgba(0, 0, 0, 0.5); border-radius: 10px;")
        elif self.current_ratio == '16:9':
            self.preview_area.setFixedWidth(800)
            self.preview_area.setFixedHeight(450)
            self.preview_area.setStyleSheet("background-color: rgba(0, 0, 0, 0.7); border-radius: 10px;")
        else:
            self.preview_area.setFixedWidth(600)
            self.preview_area.setFixedHeight(600)
            self.preview_area.setStyleSheet("background-color: rgba(0, 0, 0, 0.6); border-radius: 10px;")
        self.video_widget.setFixedSize(self.preview_area.width() - 20, self.preview_area.height() - 20)

    def change_language(self, language):
        self.current_language = language

    def change_duration(self, duration):
        self.current_duration = duration

    def pick_color(self):
        if self.enforce_trial_restrictions():
            return
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; padding: 5px; border-radius: 5px;")

    def mark_modified(self):
        self.is_modified = True

    def process_video(self):
        if self.enforce_trial_restrictions():
            return
        if not self.video_path:
            QMessageBox.warning(self, "Error", "Please upload a video first")
            return
        aspect_ratio = self.current_ratio
        font = self.font_combo.currentText()
        color = self.color_btn.styleSheet().split('background-color: ')[1].split(';')[0]
        language = self.current_language
        duration = self.current_duration
        output_path = os.path.join('temp', 'processed.mp4')
        self.subtitles = generate_subtitles(self.video_path, language)
        self.subtitle_table.setRowCount(0)
        for start, end, text in self.subtitles:
            row = self.subtitle_table.rowCount()
            self.subtitle_table.setRowCount(row + 1)
            self.subtitle_table.setItem(row, 0, QTableWidgetItem(start))
            self.subtitle_table.setItem(row, 1, QTableWidgetItem(end))
            self.subtitle_table.setItem(row, 2, QTableWidgetItem(text))
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.process_thread = ProcessThread(self.video_path, output_path, aspect_ratio, font, color, self.subtitles, language, duration)
        self.process_thread.progress.connect(self.update_progress)
        self.process_thread.finished.connect(self.process_finished)
        self.process_thread.error.connect(self.show_error)
        self.process_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def process_finished(self, output_path):
        self.progress_bar.setVisible(False)
        self.processed_path = output_path
        self.load_video_to_player(self.processed_path)
        self.is_modified = False
        QMessageBox.information(self, "Success", "Video processed successfully")

    def show_error(self, message):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", message)

    def show_export_dialog(self):
        if self.enforce_trial_restrictions():
            return
        if not self.processed_path:
            QMessageBox.warning(self, "Error", "Please process a video first")
            return
        dialog = ExportDialog(self)
        dialog.exec()

    def export_finished(self, output_path, dialog):
        self.progress_bar.setVisible(False)
        dialog.close()
        self.is_modified = False
        QMessageBox.information(self, "Success", f"Video exported successfully at: {output_path}")

    def enter_license_key(self):
        dialog = LicenseDialog(self)
        if dialog.exec():
            key = dialog.get_license_key()
            if key == "VALID_LICENSE_KEY":
                with open(LICENSE_FILE, 'w') as f:
                    f.write(key)
                self.is_licensed = True
                self.status_label.setText("Licensed Version")
                QMessageBox.information(self, "Success", "License activated successfully!")
            else:
                QMessageBox.warning(self, "Error", "Invalid license key")

    def closeEvent(self, event):
        if self.is_modified:
            reply = QMessageBox.question(self, "Close Application",
                                         "You have unsaved changes. Are you sure you want to close?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        event.accept()