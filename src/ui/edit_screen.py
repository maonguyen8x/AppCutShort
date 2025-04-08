import os
import logging  # Thêm import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
                             QColorDialog, QFileDialog, QSlider, QFrame)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget

class EditScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.selected_color = "white"  # Default color
        self.media_player = None
        self.video_widget = None
        self.init_ui()

    def init_ui(self):
        # Main layout for the edit screen (split into left and right)
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)

        # Left side: Video player
        left_layout = QVBoxLayout()
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: #4d4d4d; border-radius: 10px;")
        self.video_widget.setFixedSize(400, 225)  # Larger size for video
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        left_layout.addWidget(self.video_widget)
        left_layout.addStretch()  # Push the video to the top
        main_layout.addLayout(left_layout)

        # Separator: Black vertical line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #000000;")  # Black separator
        main_layout.addWidget(separator)

        # Right side: Options and buttons
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        right_layout.setSpacing(15)

        # Title
        title_label = QLabel("Edit Your Video")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        right_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Aspect Ratio
        ratio_layout = QHBoxLayout()
        ratio_label = QLabel("Aspect Ratio")
        ratio_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(["9:16", "16:9", "1:1"])
        self.ratio_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px;")
        self.ratio_combo.currentTextChanged.connect(self.update_ratio)
        ratio_layout.addWidget(ratio_label)
        ratio_layout.addWidget(self.ratio_combo)
        right_layout.addLayout(ratio_layout)

        # Duration
        duration_layout = QHBoxLayout()
        duration_label = QLabel("Duration")
        duration_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["Auto", "<30s", "30s - 60s", "60s - 90s", "90s - 3min"])
        self.duration_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px;")
        self.duration_combo.currentTextChanged.connect(self.update_duration)
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_combo)
        right_layout.addLayout(duration_layout)

        # Font
        font_layout = QHBoxLayout()
        font_label = QLabel("Font")
        font_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial.ttf", "TimesNewRoman.ttf", "Helvetica.ttf"])
        self.font_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px;")
        self.font_combo.currentTextChanged.connect(self.update_font)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_combo)
        right_layout.addLayout(font_layout)

        # Font Size (Slider with increase/decrease buttons and value display)
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("Font Size")
        font_size_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setMinimum(16)
        self.font_size_slider.setMaximum(48)
        self.font_size_slider.setValue(24)  # Default value
        self.font_size_slider.setTickInterval(8)
        self.font_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.font_size_slider.setMaximumWidth(100)  # Shorter slider
        self.font_size_slider.valueChanged.connect(self.update_font_size)
        self.font_size_decrease_btn = QPushButton("−")
        self.font_size_decrease_btn.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px;")
        self.font_size_decrease_btn.clicked.connect(self.decrease_font_size)
        self.font_size_increase_btn = QPushButton("+")
        self.font_size_increase_btn.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px;")
        self.font_size_increase_btn.clicked.connect(self.increase_font_size)
        self.font_size_value_label = QLabel("24")  # Display current font size
        self.font_size_value_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_decrease_btn)
        font_size_layout.addWidget(self.font_size_slider)
        font_size_layout.addWidget(self.font_size_increase_btn)
        font_size_layout.addWidget(self.font_size_value_label)
        right_layout.addLayout(font_size_layout)

        # Text Pick Color
        color_layout = QHBoxLayout()
        color_label = QLabel("Text Color")
        color_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.color_btn = QPushButton("Pick Color")
        self.color_btn.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px;")
        self.color_btn.clicked.connect(self.pick_color)
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_btn)
        right_layout.addLayout(color_layout)

        # Background Music
        music_layout = QHBoxLayout()
        music_label = QLabel("Background Music")
        music_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.music_btn = QPushButton("Add Music")
        self.music_btn.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px;")
        self.music_btn.clicked.connect(self.add_background_music)
        music_layout.addWidget(music_label)
        music_layout.addWidget(self.music_btn)
        right_layout.addLayout(music_layout)

        # Music file label (timeline placeholder)
        self.music_file_label = QLabel("No music selected")
        self.music_file_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        right_layout.addWidget(self.music_file_label)

        # Volume Control
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume")
        volume_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)  # 0.0
        self.volume_slider.setMaximum(200)  # 2.0
        self.volume_slider.setValue(100)  # Default 1.0
        self.volume_slider.setTickInterval(20)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.valueChanged.connect(self.update_volume)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        right_layout.addLayout(volume_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Export button (green, shorter)
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("background-color: #22c55e; padding: 8px 10px; border-radius: 5px; font-size: 12px;")  # Shorter
        export_btn.clicked.connect(self.parent.show_export_dialog)
        button_layout.addWidget(export_btn)

        # Close button (red, shorter)
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #ef4444; padding: 8px 10px; border-radius: 5px; font-size: 12px;")  # Shorter
        close_btn.clicked.connect(self.close_screen)
        button_layout.addWidget(close_btn)

        right_layout.addLayout(button_layout)
        main_layout.addLayout(right_layout)

        # Set stretch factors to make left side wider
        main_layout.setStretch(0, 6)  # Left side (video) takes 60%
        main_layout.setStretch(2, 4)  # Right side (options) takes 40%

        # Load video
        self.load_video()

    def load_video(self):
        # Load the video from local path or downloaded path
        video_path = None
        if self.parent.local_video_path:
            video_path = self.parent.local_video_path
        elif os.path.exists(os.path.join('temp', 'downloaded_video.mp4')):
            video_path = os.path.join('temp', 'downloaded_video.mp4')

        if video_path and os.path.exists(video_path):
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.play()
            # Kiểm tra trạng thái của QMediaPlayer
            self.media_player.errorOccurred.connect(lambda error: logging.error(f"QMediaPlayer error: {error}"))
            self.media_player.mediaStatusChanged.connect(lambda status: logging.info(f"QMediaPlayer status: {status}"))
        else:
            logging.warning(f"Video path not found: {video_path}")
            self.video_widget.setStyleSheet("background-color: #4d4d4d; border-radius: 10px; color: #aaaaaa; font-size: 16px;")
            self.video_widget.setFixedSize(400, 225)

    def update_ratio(self, ratio):
        self.parent.current_ratio = ratio
        # Update video widget size based on aspect ratio
        if ratio == "16:9":
            self.video_widget.setFixedSize(400, 225)  # 16:9 ratio
        elif ratio == "9:16":
            self.video_widget.setFixedSize(225, 400)  # 9:16 ratio
        elif ratio == "1:1":
            self.video_widget.setFixedSize(300, 300)  # 1:1 ratio

    def update_duration(self, duration):
        self.parent.current_duration = duration

    def update_font(self, font):
        self.parent.current_font = font

    def update_font_size(self):
        font_size = self.font_size_slider.value()
        self.parent.current_font_size = font_size
        self.font_size_value_label.setText(str(font_size))  # Update displayed value

    def increase_font_size(self):
        current_value = self.font_size_slider.value()
        self.font_size_slider.setValue(min(current_value + 8, 48))

    def decrease_font_size(self):
        current_value = self.font_size_slider.value()
        self.font_size_slider.setValue(max(current_value - 8, 16))

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.parent.current_color = self.selected_color
            self.color_btn.setStyleSheet(f"background-color: {self.selected_color}; padding: 5px; border-radius: 5px; font-size: 14px;")

    def add_background_music(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Music", "", "Audio Files (*.mp3 *.wav)")
        if file_path:
            self.parent.current_background_music = file_path
            self.music_file_label.setText(os.path.basename(file_path))

    def update_volume(self):
        self.parent.current_volume = self.volume_slider.value() / 100.0

    def close_screen(self):
        self.media_player.stop()  # Stop the video when closing
        self.parent.initial_screen.setVisible(True)
        self.setVisible(False)
        self.parent.status_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")