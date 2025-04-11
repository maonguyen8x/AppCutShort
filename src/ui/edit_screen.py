import os
import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
                             QColorDialog, QFileDialog, QSlider, QFrame, QLineEdit, QTabWidget,
                             QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem)
from PyQt6.QtCore import Qt, QUrl, QSize, QRectF, QPointF, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QMouseEvent, QDragEnterEvent, QDropEvent
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

class Command:
    def __init__(self, execute_func, undo_func, data):
        self.execute_func = execute_func
        self.undo_func = undo_func
        self.data = data

    def execute(self):
        self.execute_func(self.data)

    def undo(self):
        self.undo_func(self.data)

class UndoRedoStack:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def execute(self, command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)

    def redo(self):
        if not self.redo_stack:
            return
        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)

class TimelineTrack(QGraphicsRectItem):
    def __init__(self, name, start, duration, parent=None):
        super().__init__(start * 10, 0, duration * 10, 40)  # 1 second = 10 pixels
        self.name = name
        self.start = start
        self.duration = duration
        self.setBrush(QColor("#3d3d3d"))
        self.setPen(QPen(QColor("#4d4d4d"), 1))
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.setPen(QPen(QColor("#aaaaaa"), 1))
        painter.drawText(self.boundingRect().adjusted(10, 0, 0, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.name)

class TimelineView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setStyleSheet("background-color: #2d2d2d; border: 1px solid #4d4d4d;")
        self.setMinimumHeight(200)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.init_timeline()
        self.playhead_pos = 0
        self.playhead = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_playhead)
        self.timer.setInterval(100)  # Update every 100ms

    def init_timeline(self):
        # Add timeline ruler (time markers)
        total_duration = 300  # 5 minutes max
        for i in range(0, total_duration, 10):  # Mark every 10 seconds
            line = QGraphicsLineItem(i * 10, -20, i * 10, 0)
            line.setPen(QPen(QColor("#aaaaaa"), 1))
            self.scene.addItem(line)
            text = self.scene.addText(f"{i}s")
            text.setDefaultTextColor(QColor("#aaaaaa"))
            text.setPos(i * 10 - 10, -40)

        # Add playhead
        self.playhead = QGraphicsLineItem(0, -20, 0, 160)
        self.playhead.setPen(QPen(QColor("#3b82f6"), 2))
        self.scene.addItem(self.playhead)

        # Initial tracks
        self.video_track = TimelineTrack("Video", 0, 60)
        self.audio_track = TimelineTrack("Audio", 0, 60)
        self.text_track = TimelineTrack("Text", 0, 0)
        self.logo_track = TimelineTrack("Logo", 0, 0)

        self.scene.addItem(self.video_track)
        self.scene.addItem(self.audio_track)
        self.scene.addItem(self.text_track)
        self.scene.addItem(self.logo_track)

        self.video_track.setPos(0, 0)
        self.audio_track.setPos(0, 40)
        self.text_track.setPos(0, 80)
        self.logo_track.setPos(0, 120)

        self.scene.setSceneRect(0, -40, total_duration * 10, 200)

    def start_playback(self):
        self.timer.start()

    def stop_playback(self):
        self.timer.stop()

    def update_playhead(self):
        self.playhead_pos += 0.1  # Move 0.1 seconds per update
        self.playhead.setLine(self.playhead_pos * 10, -20, self.playhead_pos * 10, 160)
        # Update video position
        if self.parent().player:
            self.parent().player.setPosition(int(self.playhead_pos * 1000))

class LogoOverlay(QLabel):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setPixmap(pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio))
        self.setStyleSheet("border: 2px solid #3b82f6; border-radius: 25px; background-color: rgba(0, 0, 0, 0.5);")
        self.setFixedSize(50, 50)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        self.dragging = False
        self.offset = QPointF()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            new_pos = event.pos() - self.offset + self.pos()
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

class PreviewArea(QVideoWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #2d2d2d; border-radius: 10px;")
        self.setMinimumSize(640, 360)
        self.setMaximumSize(640, 360)
        self.setAcceptDrops(True)
        self.logos = []

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText() and event.mimeData().text().startswith("logo:"):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        logo_path = event.mimeData().text().replace("logo:", "")
        pixmap = QPixmap(logo_path)
        logo = LogoOverlay(pixmap, self)
        logo.move(event.pos() - QPointF(25, 25))  # Center the logo at drop position
        logo.show()
        self.logos.append(logo)

class EditScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.selected_color = "white"
        self.audio_files = []
        self.logo_pixmap = None
        self.preview_area = None
        self.player = None
        self.undo_redo = UndoRedoStack()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        new_project_btn = QPushButton("New Project")
        new_project_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        new_project_btn.clicked.connect(self.parent.new_project)
        undo_btn = QPushButton("Undo")
        undo_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        undo_btn.clicked.connect(self.undo)
        redo_btn = QPushButton("Redo")
        redo_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        redo_btn.clicked.connect(self.redo)
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("background-color: #22c55e; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        export_btn.clicked.connect(self.parent.show_export_dialog)
        toolbar.addWidget(new_project_btn)
        toolbar.addWidget(undo_btn)
        toolbar.addWidget(redo_btn)
        toolbar.addStretch()
        toolbar.addWidget(export_btn)
        main_layout.addLayout(toolbar)

        # Main content
        content_layout = QHBoxLayout()

        # Left: Preview and timeline
        left_layout = QVBoxLayout()
        preview_container = QFrame()
        preview_container.setStyleSheet("background-color: #1a1a1a; border-radius: 10px;")
        preview_container_layout = QVBoxLayout(preview_container)
        preview_container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_area = PreviewArea()
        preview_container_layout.addWidget(self.preview_area)
        left_layout.addWidget(preview_container)

        # Playback controls
        playback_layout = QHBoxLayout()
        play_btn = QPushButton("Play")
        play_btn.setStyleSheet("background-color: #3b82f6; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        play_btn.clicked.connect(self.play_video)
        pause_btn = QPushButton("Pause")
        pause_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        pause_btn.clicked.connect(self.pause_video)
        playback_layout.addStretch()
        playback_layout.addWidget(play_btn)
        playback_layout.addWidget(pause_btn)
        playback_layout.addStretch()
        left_layout.addLayout(playback_layout)

        # Timeline
        self.timeline_view = TimelineView(self)
        left_layout.addWidget(self.timeline_view)

        content_layout.addLayout(left_layout)

        # Right: Edit panel
        edit_panel = QTabWidget()
        edit_panel.setStyleSheet("""
            QTabWidget::pane { background-color: #2d2d2d; border: 1px solid #3d3d3d; }
            QTabBar::tab { background-color: #3d3d3d; color: white; padding: 8px 16px; }
            QTabBar::tab:selected { background-color: #3b82f6; }
        """)

        # Video Tab
        video_tab = QWidget()
        video_layout = QVBoxLayout(video_tab)
        video_layout.setSpacing(10)

        ratio_layout = QHBoxLayout()
        ratio_label = QLabel("Aspect Ratio")
        ratio_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(["9:16", "16:9", "1:1"])
        self.ratio_combo.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        self.ratio_combo.setMinimumWidth(100)
        self.ratio_combo.currentTextChanged.connect(self.update_ratio)
        ratio_layout.addWidget(ratio_label)
        ratio_layout.addWidget(self.ratio_combo)
        video_layout.addLayout(ratio_layout)

        duration_layout = QHBoxLayout()
        duration_label = QLabel("Duration")
        duration_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["Auto", "<30s", "30s - 60s", "60s - 90s", "90s - 3min"])
        self.duration_combo.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        self.duration_combo.setMinimumWidth(100)
        self.duration_combo.currentTextChanged.connect(self.update_duration)
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_combo)
        video_layout.addLayout(duration_layout)

        trim_layout = QHBoxLayout()
        trim_label = QLabel("Trim Video")
        trim_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.trim_start = QLineEdit("0")
        self.trim_start.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        self.trim_end = QLineEdit("60")
        self.trim_end.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        trim_btn = QPushButton("Apply")
        trim_btn.setStyleSheet("background-color: #3b82f6; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        trim_btn.clicked.connect(self.trim_video)
        trim_layout.addWidget(trim_label)
        trim_layout.addWidget(self.trim_start)
        trim_layout.addWidget(self.trim_end)
        trim_layout.addWidget(trim_btn)
        video_layout.addLayout(trim_layout)

        edit_panel.addTab(video_tab, "Video")

        # Text Tab
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        text_layout.setSpacing(10)

        font_layout = QHBoxLayout()
        font_label = QLabel("Font")
        font_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial.ttf", "TimesNewRoman.ttf", "Helvetica.ttf"])
        self.font_combo.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        self.font_combo.setMinimumWidth(100)
        self.font_combo.currentTextChanged.connect(self.update_font)
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_combo)
        text_layout.addLayout(font_layout)

        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("Font Size")
        font_size_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setMinimum(16)
        self.font_size_slider.setMaximum(48)
        self.font_size_slider.setValue(24)
        self.font_size_slider.setTickInterval(8)
        self.font_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.font_size_slider.setMinimumWidth(100)
        self.font_size_slider.valueChanged.connect(self.update_font_size)
        self.font_size_value_label = QLabel("24")
        self.font_size_value_label.setStyleSheet("font-size: 14px; color: #aaaaaa;")
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_slider)
        font_size_layout.addWidget(self.font_size_value_label)
        text_layout.addLayout(font_size_layout)

        color_layout = QHBoxLayout()
        color_label = QLabel("Text Color")
        color_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.color_btn = QPushButton("Pick")
        self.color_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        self.color_btn.setMinimumWidth(60)
        self.color_btn.clicked.connect(self.pick_color)
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_btn)
        text_layout.addLayout(color_layout)

        effect_layout = QHBoxLayout()
        effect_label = QLabel("Text Effect")
        effect_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.text_effect_combo = QComboBox()
        self.text_effect_combo.addItems(["None", "3D", "Shadow", "Glow"])
        self.text_effect_combo.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        self.text_effect_combo.setMinimumWidth(100)
        self.text_effect_combo.currentTextChanged.connect(self.update_text_effect)
        effect_layout.addWidget(effect_label)
        effect_layout.addWidget(self.text_effect_combo)
        text_layout.addLayout(effect_layout)

        edit_panel.addTab(text_tab, "Text")

        # Audio Tab
        audio_tab = QWidget()
        audio_layout = QVBoxLayout(audio_tab)
        audio_layout.setSpacing(10)

        music_layout = QHBoxLayout()
        music_label = QLabel("Background Music")
        music_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.music_btn = QPushButton("Add")
        self.music_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        self.music_btn.setMinimumWidth(60)
        self.music_btn.clicked.connect(self.add_background_music)
        music_layout.addWidget(music_label)
        music_layout.addWidget(self.music_btn)
        audio_layout.addLayout(music_layout)

        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume")
        volume_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(200)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickInterval(20)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setMinimumWidth(100)
        self.volume_slider.valueChanged.connect(self.update_volume)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        audio_layout.addLayout(volume_layout)

        edit_panel.addTab(audio_tab, "Audio")

        # Logo Tab
        logo_tab = QWidget()
        logo_layout = QVBoxLayout(logo_tab)
        logo_layout.setSpacing(10)

        add_logo_layout = QHBoxLayout()
        logo_label = QLabel("Logo")
        logo_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.logo_btn = QPushButton("Add")
        self.logo_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        self.logo_btn.setMinimumWidth(60)
        self.logo_btn.clicked.connect(self.add_logo)
        add_logo_layout.addWidget(logo_label)
        add_logo_layout.addWidget(self.logo_btn)
        logo_layout.addLayout(add_logo_layout)

        self.logo_preview = QLabel("No logo selected")
        self.logo_preview.setStyleSheet("background-color: #3d3d3d; border-radius: 5px; color: #aaaaaa; font-size: 12px;")
        self.logo_preview.setMinimumHeight(50)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setAcceptDrops(False)
        self.logo_preview.setMouseTracking(True)
        logo_layout.addWidget(self.logo_preview)

        edit_panel.addTab(logo_tab, "Logo")

        content_layout.addWidget(edit_panel)

        content_layout.setStretch(0, 7)
        content_layout.setStretch(1, 3)
        main_layout.addLayout(content_layout)

    def load_video(self, video_path):
        self.player = QMediaPlayer()
        audio_output = QAudioOutput()
        self.player.setAudioOutput(audio_output)
        self.player.setVideoOutput(self.preview_area)
        self.player.setSource(QUrl.fromLocalFile(video_path))
        self.player.play()
        self.timeline_view.start_playback()

    def play_video(self):
        if self.player:
            self.player.play()
            self.timeline_view.start_playback()

    def pause_video(self):
        if self.player:
            self.player.pause()
            self.timeline_view.stop_playback()

    def update_ratio(self, ratio):
        def execute(data):
            self.parent.current_ratio = data
            if data == "16:9":
                self.preview_area.setMinimumSize(640, 360)
                self.preview_area.setMaximumSize(640, 360)
            elif data == "9:16":
                self.preview_area.setMinimumSize(360, 640)
                self.preview_area.setMaximumSize(360, 640)
            elif data == "1:1":
                self.preview_area.setMinimumSize(480, 480)
                self.preview_area.setMaximumSize(480, 480)

        def undo(data):
            previous_ratio = self.parent.current_ratio
            self.parent.current_ratio = data
            if previous_ratio == "16:9":
                self.preview_area.setMinimumSize(640, 360)
                self.preview_area.setMaximumSize(640, 360)
            elif previous_ratio == "9:16":
                self.preview_area.setMinimumSize(360, 640)
                self.preview_area.setMaximumSize(360, 640)
            elif previous_ratio == "1:1":
                self.preview_area.setMinimumSize(480, 480)
                self.preview_area.setMaximumSize(480, 480)

        previous_ratio = self.parent.current_ratio
        command = Command(execute, undo, ratio)
        self.undo_redo.execute(command)

    def update_duration(self, duration):
        self.parent.current_duration = duration

    def update_font(self, font):
        self.parent.current_font = font

    def update_font_size(self):
        font_size = self.font_size_slider.value()
        self.parent.current_font_size = font_size
        self.font_size_value_label.setText(str(font_size))

    def update_text_effect(self, effect):
        self.parent.current_caption_effect = effect
        logging.info(f"Text effect updated to: {effect}")

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
            self.audio_files.append(file_path)

    def add_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Image Files (*.png *.jpg *.jpeg)")
        if file_path:
            self.parent.icons.append(file_path)
            self.logo_pixmap = QPixmap(file_path).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)
            self.logo_preview.setPixmap(self.logo_pixmap)
            self.logo_preview.setStyleSheet("border: 2px solid #3b82f6; border-radius: 25px; background-color: rgba(0, 0, 0, 0.5);")

    def update_volume(self):
        self.parent.current_volume = self.volume_slider.value() / 100.0

    def trim_video(self):
        start = float(self.trim_start.text())
        end = float(self.trim_end.text())
        if start >= end:
            QMessageBox.warning(self, "Error", "Start time must be less than end time.")
            return

        from src.utils.video_processor import trim_video
        temp_path = os.path.join('temp', 'trimmed_video.mp4')
        success = trim_video(self.parent.local_video_path, temp_path, start, end)
        if success:
            self.parent.local_video_path = temp_path
            self.load_video(temp_path)
            self.timeline_view.video_track.duration = end - start
            self.timeline_view.video_track.setRect(start * 10, 0, (end - start) * 10, 40)
        else:
            QMessageBox.critical(self, "Error", "Failed to trim video. Check logs for details.")

    def undo(self):
        self.undo_redo.undo()

    def redo(self):
        self.undo_redo.redo()