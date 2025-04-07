import os
import logging
import warnings
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
                             QMessageBox, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFileDialog, QColorDialog, QStackedWidget, QSpinBox, QSlider)
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl, QPoint
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtGui import QPixmap, QMouseEvent
import platform
from src.utils.youtube_downloader import download_youtube_video, get_youtube_stream_url
from src.ui.subtitle_dialog import SubtitleDialog
from src.ui.export_dialog import ExportDialog
from src.ui.license_dialog import LicenseDialog
from src.processing.process_thread import ProcessThread
from src.processing.ai_processor import generate_subtitles, translate_subtitles

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename='appcutshort.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress FutureWarning from whisper
warnings.filterwarnings("ignore", category=FutureWarning, message=".*weights_only=False.*")

TRIAL_DAYS = 7
TRIAL_START_FILE = "trial_start.txt"
LICENSE_FILE = "license.key"

class VideoEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AppCutShort")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("background-color: #2d2d2d; color: white;")
        self.video_path = None  # Store stream URL for preview
        self.local_video_path = None  # Store local path after downloading (during export)
        self.processed_path = None
        self.subtitles = []
        self.is_modified = False
        self.current_ratio = '16:9'
        self.current_language = 'English'
        self.current_duration = 'Auto'
        self.current_font = 'Arial'
        self.current_color = '#ffffff'
        self.current_font_size = 24
        self.current_template = 'Default'
        self.current_volume = 1.0
        self.current_audio_effect = 'None'
        self.current_background_music = None
        self.current_caption_effect = 'None'
        self.current_color_filter = 'None'
        self.icons = []
        self.is_trial_active = self.check_trial_period()
        self.is_licensed = self.check_license()
        self.init_ui()
        self.setAcceptDrops(True)

    def get_font_path(self):
        # Determine font path based on OS
        if os.name == 'nt':  # Windows
            return f'C:\\Windows\\Fonts\\{self.current_font}.ttf'
        elif platform.system() == 'Darwin':  # macOS
            return f'/Library/Fonts/{self.current_font}.ttf'
        else:  # Linux
            return '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # Menu bar
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
        menu_bar.addWidget(title_label)
        menu_bar.addStretch()
        menu_bar.addWidget(import_btn)
        menu_bar.addWidget(export_btn)
        menu_bar.addWidget(license_btn)
        self.main_layout.addLayout(menu_bar)

        # Stacked widget for screen switching
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # Initial screen
        self.initial_screen = QWidget()
        self.init_initial_screen()
        self.stacked_widget.addWidget(self.initial_screen)

        # Edit screen
        self.edit_screen = QWidget()
        self.init_edit_screen()
        self.stacked_widget.addWidget(self.edit_screen)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("margin-top: 10px;")
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

        # Progress label for "Continue" button
        self.continue_progress_label = QLabel("Progress: 0%")
        self.continue_progress_label.setStyleSheet("color: #3b82f6; font-weight: bold; margin-top: 5px;")
        self.continue_progress_label.setVisible(False)
        self.main_layout.addWidget(self.continue_progress_label)

        # Status label
        self.status_label = QLabel(self.get_status_text())
        self.status_label.setStyleSheet("font-size: 12px; color: #aaaaaa;")
        self.main_layout.addWidget(self.status_label)

    def init_initial_screen(self):
        layout = QVBoxLayout(self.initial_screen)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # URL input
        url_label = QLabel("YouTube URL")
        url_label.setStyleSheet("font-weight: bold;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; width: 400px;")
        self.url_input.textChanged.connect(self.load_thumbnail)
        layout.addWidget(url_label)
        layout.addWidget(self.url_input)

        # Thumbnail display
        self.thumbnail_label = QLabel("No thumbnail loaded")
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setStyleSheet("color: gray; margin: 20px;")
        layout.addWidget(self.thumbnail_label)

        # Buttons
        button_layout = QHBoxLayout()
        upload_btn = QPushButton("Upload")
        upload_btn.setStyleSheet("background-color: #3b82f6; padding: 10px; border-radius: 5px; width: 100px;")
        upload_btn.clicked.connect(self.load_video)
        continue_btn = QPushButton("Continue")
        continue_btn.setStyleSheet("background-color: #3b82f6; padding: 10px; border-radius: 5px; width: 100px;")
        continue_btn.clicked.connect(self.switch_to_edit_screen)
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #ef4444; padding: 10px; border-radius: 5px; width: 100px;")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(upload_btn)
        button_layout.addWidget(continue_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def init_edit_screen(self):
        layout = QHBoxLayout(self.edit_screen)

        # Video preview area
        self.preview_area = QFrame()
        self.preview_area.setStyleSheet("background-color: rgba(0, 0, 0, 0.7); border-radius: 10px;")
        self.preview_area.setFixedWidth(800)
        preview_layout = QVBoxLayout(self.preview_area)
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.video_widget.mousePressEvent = self.handle_icon_position
        self.player = QMediaPlayer()
        self.player.setVideoOutput(self.video_widget)
        preview_layout.addWidget(self.video_widget)
        self.update_preview_size()
        layout.addWidget(self.preview_area)

        # Edit panel
        edit_panel = QFrame()
        edit_panel.setStyleSheet("background-color: #3d3d3d; border-radius: 10px; padding: 10px;")
        edit_layout = QVBoxLayout(edit_panel)

        # Aspect ratio selection
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

        # Language selection
        language_label = QLabel("Language")
        language_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.language_combo = QComboBox()
        self.language_combo.addItems(['English', 'Vietnamese', 'Japanese'])
        self.language_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.language_combo.currentTextChanged.connect(self.change_language)
        edit_layout.addWidget(language_label)
        edit_layout.addWidget(self.language_combo)

        # Duration selection
        duration_label = QLabel("Video Duration")
        duration_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(['Auto', '<30s', '30s - 60s', '60s - 90s', '90s - 3min'])
        self.duration_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.duration_combo.currentTextChanged.connect(self.change_duration)
        edit_layout.addWidget(duration_label)
        edit_layout.addWidget(self.duration_combo)

        # Font selection
        font_label = QLabel("Font")
        font_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.font_combo = QComboBox()
        self.font_combo.addItems(['Arial', 'Times New Roman', 'Helvetica', 'Calibri', 'Roboto', 'Montserrat'])
        self.font_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.font_combo.currentTextChanged.connect(self.update_caption_style)
        edit_layout.addWidget(font_label)
        edit_layout.addWidget(self.font_combo)

        # Font size selection
        font_size_label = QLabel("Font Size")
        font_size_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(10, 100)
        self.font_size_spinbox.setValue(self.current_font_size)
        self.font_size_spinbox.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.font_size_spinbox.valueChanged.connect(self.update_caption_style)
        edit_layout.addWidget(font_size_label)
        edit_layout.addWidget(self.font_size_spinbox)

        # Caption color picker
        color_label = QLabel("Caption Color")
        color_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.color_btn = QPushButton("Pick Color")
        self.color_btn.setStyleSheet("background-color: #ffffff; padding: 5px; border-radius: 5px;")
        self.color_btn.clicked.connect(self.pick_color)
        edit_layout.addWidget(color_label)
        edit_layout.addWidget(self.color_btn)

        # Caption effect selection
        caption_effect_label = QLabel("Caption Effect")
        caption_effect_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.caption_effect_combo = QComboBox()
        self.caption_effect_combo.addItems(['None', 'Fade', 'Move', 'Shadow'])
        self.caption_effect_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.caption_effect_combo.currentTextChanged.connect(self.update_caption_effect)
        edit_layout.addWidget(caption_effect_label)
        edit_layout.addWidget(self.caption_effect_combo)

        # Template selection
        template_label = QLabel("Template")
        template_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.template_combo = QComboBox()
        self.template_combo.addItems(['Default', 'Modern', 'Classic', 'Minimal'])
        self.template_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.template_combo.currentTextChanged.connect(self.update_template)
        edit_layout.addWidget(template_label)
        edit_layout.addWidget(self.template_combo)

        # Volume adjustment
        volume_label = QLabel("Volume")
        volume_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 200)  # 0% to 200% volume
        self.volume_slider.setValue(100)  # Default 100%
        self.volume_slider.valueChanged.connect(self.update_volume)
        edit_layout.addWidget(volume_label)
        edit_layout.addWidget(self.volume_slider)

        # Audio effect selection
        audio_effect_label = QLabel("Audio Effect")
        audio_effect_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.audio_effect_combo = QComboBox()
        self.audio_effect_combo.addItems(['None', 'Echo', 'Reverb'])
        self.audio_effect_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.audio_effect_combo.currentTextChanged.connect(self.update_audio_effect)
        edit_layout.addWidget(audio_effect_label)
        edit_layout.addWidget(self.audio_effect_combo)

        # Background music
        bg_music_label = QLabel("Background Music")
        bg_music_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        bg_music_btn = QPushButton("Add Background Music")
        bg_music_btn.setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
        bg_music_btn.clicked.connect(self.add_background_music)
        edit_layout.addWidget(bg_music_label)
        edit_layout.addWidget(bg_music_btn)

        # Color filter selection
        color_filter_label = QLabel("Color Filter")
        color_filter_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.color_filter_combo = QComboBox()
        self.color_filter_combo.addItems(['None', 'Bright', 'Contrast', 'Vintage', 'Cinematic'])
        self.color_filter_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        self.color_filter_combo.currentTextChanged.connect(self.update_color_filter)
        edit_layout.addWidget(color_filter_label)
        edit_layout.addWidget(self.color_filter_combo)

        # Icon/sticker drag-and-drop hint
        icon_label = QLabel("Drag and Drop Icons/Stickers onto Video")
        icon_label.setStyleSheet("font-weight: bold; margin-top: 10px; color: #aaaaaa;")
        edit_layout.addWidget(icon_label)

        edit_layout.addStretch()
        layout.addWidget(edit_panel)

    def load_thumbnail(self, url):
        if self.enforce_trial_restrictions():
            return
        if url.startswith("https://www.youtube.com/") or url.startswith("https://youtu.be/"):
            thumbnail_path = download_youtube_video(url, thumbnail_only=True)
            if thumbnail_path and os.path.exists(thumbnail_path):
                pixmap = QPixmap(thumbnail_path)
                self.thumbnail_label.setPixmap(pixmap.scaled(400, 300, Qt.AspectRatioMode.KeepAspectRatio))
                self.thumbnail_label.setVisible(True)
            else:
                self.thumbnail_label.setText("Failed to load thumbnail")
                self.thumbnail_label.setVisible(True)

    def load_video(self):
        if self.enforce_trial_restrictions():
            return
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
            return
        self.video_path = get_youtube_stream_url(url)
        if self.video_path:
            self.load_video_to_player(self.video_path)
        else:
            QMessageBox.critical(self, "Error", "Failed to load video stream")

    def update_continue_progress(self, value):
        # Update the progress label for the "Continue" button
        self.continue_progress_label.setText(f"Progress: {value}%")
        self.progress_bar.setValue(value)

    def switch_to_edit_screen(self):
        if self.enforce_trial_restrictions():
            return
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
            return

        # Get the streaming URL for preview
        self.video_path = get_youtube_stream_url(url)
        if not self.video_path:
            QMessageBox.critical(self, "Error", "Failed to retrieve YouTube stream")
            return

        logging.info(f"Streaming URL loaded: {self.video_path}")
        self.load_video_to_player(self.video_path)
        self.stacked_widget.setCurrentWidget(self.edit_screen)

        # Show progress bar and label
        self.progress_bar.setVisible(True)
        self.continue_progress_label.setVisible(True)
        self.progress_bar.setValue(0)
        self.continue_progress_label.setText("Progress: 0%")
        self.status_label.setText("Generating subtitles...")

        # Generate subtitles using the streaming URL
        try:
            self.subtitles = generate_subtitles(self.video_path, self.current_language, self.update_continue_progress)
            logging.info("Subtitles generated successfully")
            self.status_label.setText("Preview loaded. Export to process video.")
        except Exception as e:
            logging.error(f"Error generating subtitles: {str(e)}")
            self.show_error(f"Failed to generate subtitles: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
            self.continue_progress_label.setVisible(False)

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
            self.local_video_path = file_path
            self.video_path = file_path  # For local files, use the same path for preview
            self.load_video_to_player(self.video_path)
            self.stacked_widget.setCurrentWidget(self.edit_screen)
            self.subtitles = generate_subtitles(self.local_video_path, self.current_language, self.update_continue_progress)
            self.update_video_preview()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if self.enforce_trial_restrictions():
            return
        urls = event.mimeData().urls()
        for url in urls:
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                self.local_video_path = file_path
                self.video_path = file_path
                self.load_video_to_player(self.video_path)
                self.stacked_widget.setCurrentWidget(self.edit_screen)
                self.subtitles = generate_subtitles(self.local_video_path, self.current_language, self.update_continue_progress)
                self.update_video_preview()
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                pos = event.position()
                self.icons.append({'path': file_path, 'x': pos.x(), 'y': pos.y()})
                self.update_video_preview()

    def handle_icon_position(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self.icons:
            pos = event.position()
            self.icons[-1]['x'] = pos.x()
            self.icons[-1]['y'] = pos.y()
            self.update_video_preview()

    def load_video_to_player(self, video_path):
        # Load video (stream URL or local path) into player
        self.player.setSource(QUrl(video_path))
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
        self.status_label.setText("Aspect ratio changed. Export to process video.")

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
        self.subtitles = translate_subtitles(self.subtitles, language)
        self.status_label.setText("Language changed. Export to process video.")

    def change_duration(self, duration):
        self.current_duration = duration
        self.status_label.setText("Duration changed. Export to process video.")

    def pick_color(self):
        if self.enforce_trial_restrictions():
            return
        color = QColorDialog.getColor()
        if color.isValid():
            self.current_color = color.name()
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; padding: 5px; border-radius: 5px;")
            self.status_label.setText("Caption color changed. Export to process video.")

    def update_caption_style(self):
        self.current_font = self.font_combo.currentText()
        self.current_font_size = self.font_size_spinbox.value()
        self.status_label.setText("Caption style changed. Export to process video.")

    def update_caption_effect(self, effect):
        self.current_caption_effect = effect
        self.status_label.setText("Caption effect changed. Export to process video.")

    def update_template(self, template):
        self.current_template = template
        self.status_label.setText("Template changed. Export to process video.")

    def update_volume(self, value):
        try:
            self.current_volume = value / 100.0
            logging.info(f"Volume updated to: {self.current_volume}")
            self.status_label.setText("Volume changed. Export to process video.")
        except Exception as e:
            logging.error(f"Error updating volume: {str(e)}")
            self.show_error(f"Failed to update volume: {str(e)}")

    def update_audio_effect(self, effect):
        self.current_audio_effect = effect
        self.status_label.setText("Audio effect changed. Export to process video.")

    def add_background_music(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Music", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.current_background_music = file_path
            self.status_label.setText("Background music added. Export to process video.")

    def update_color_filter(self, filter):
        self.current_color_filter = filter
        self.status_label.setText("Color filter changed. Export to process video.")

    def update_video_preview(self):
        # Skip processing since we don't have a local file yet
        self.status_label.setText("Preview updated. Export to process video.")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def mark_modified(self):
        self.is_modified = True

    def show_export_dialog(self):
        if self.enforce_trial_restrictions():
            return
        if not self.video_path:
            QMessageBox.warning(self, "Error", "Please load a video first")
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

    def show_error(self, message):
        self.progress_bar.setVisible(False)
        self.continue_progress_label.setVisible(False)
        self.status_label.setText(self.get_status_text())
        logging.error(f"Error: {message}")
        QMessageBox.critical(self, "Error", message)

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