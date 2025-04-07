import sys
import os
import subprocess
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QProgressBar,
                             QMessageBox, QFrame, QColorDialog, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDialog, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pytube import YouTube

# class ProcessThread(QThread):
#     progress = pyqtSignal(int)
#     finished = pyqtSignal(str)
#     error = pyqtSignal(str)

#     def __init__(self, input_path, output_path, aspect_ratio, font, color, subtitles):
#         super().__init__()
#         self.input_path = input_path
#         self.output_path = output_path
#         self.aspect_ratio = aspect_ratio
#         self.font = font
#         self.color = color
#         self.subtitles = subtitles

#     def run(self):
#         try:
#             # Tạo file subtitle từ danh sách phụ đề
#             subtitle_path = os.path.join('temp', 'subtitle.srt')
#             with open(subtitle_path, 'w', encoding='utf-8') as f:
#                 for i, (start, end, text) in enumerate(self.subtitles, 1):
#                     f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

#             # Xác định tỷ lệ khung hình
#             if self.aspect_ratio == '9:16':
#                 scale = 'scale=1080:1920'
#             elif self.aspect_ratio == '16:9':
#                 scale = 'scale=1920:1080'
#             else:
#                 scale = 'scale=1080:1080'

#             # Chuyển đổi màu HEX sang định dạng FFmpeg
#             color = self.color.lstrip('#')
#             color = f"&H{color}"

#             # Lệnh FFmpeg
#             cmd = [
#                 'ffmpeg', '-i', self.input_path,
#                 '-vf', f"{scale},subtitles={subtitle_path}:force_style='FontName={self.font},PrimaryColour={color}'",
#                 '-y', self.output_path
#             ]

#             process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
#             duration = None
#             for line in process.stdout:
#                 if duration is None and 'Duration' in line:
#                     match = re.search(r'Duration: (\d+):(\d+):(\d+.\d+)', line)
#                     if match:
#                         hours, minutes, seconds = map(float, match.groups())
#                         duration = hours * 3600 + minutes * 60 + seconds
#                 if 'time=' in line and duration:
#                     match = re.search(r'time=(\d+):(\d+):(\d+.\d+)', line)
#                     if match:
#                         hours, minutes, seconds = map(float, match.groups())
#                         current_time = hours * 3600 + minutes * 60 + seconds
#                         percent = int((current_time / duration) * 100)
#                         self.progress.emit(min(percent, 100))

#             process.wait()
#             if process.returncode == 0:
#                 self.finished.emit(self.output_path)
#             else:
#                 self.error.emit("Error processing video")
#         except Exception as e:
#             self.error.emit(str(e))

# class ExportThread(QThread):
#     progress = pyqtSignal(int)
#     finished = pyqtSignal(str)
#     error = pyqtSignal(str)

#     def __init__(self, input_path, output_path, resolution):
#         super().__init__()
#         self.input_path = input_path
#         self.output_path = output_path
#         self.resolution = resolution

#     def run(self):
#         try:
#             if self.resolution == '720p':
#                 scale = 'scale=1280:720'
#             elif self.resolution == '1080p':
#                 scale = 'scale=1920:1080'
#             elif self.resolution == '2K':
#                 scale = 'scale=2560:1440'
#             else:
#                 scale = 'scale=3840:2160'

#             cmd = [
#                 'ffmpeg', '-i', self.input_path,
#                 '-vf', scale,
#                 '-y', self.output_path
#             ]

#             process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
#             duration = None
#             for line in process.stdout:
#                 if duration is None and 'Duration' in line:
#                     match = re.search(r'Duration: (\d+):(\d+):(\d+.\d+)', line)
#                     if match:
#                         hours, minutes, seconds = map(float, match.groups())
#                         duration = hours * 3600 + minutes * 60 + seconds
#                 if 'time=' in line and duration:
#                     match = re.search(r'time=(\d+):(\d+):(\d+.\d+)', line)
#                     if match:
#                         hours, minutes, seconds = map(float, match.groups())
#                         current_time = hours * 3600 + minutes * 60 + seconds
#                         percent = int((current_time / duration) * 100)
#                         self.progress.emit(min(percent, 100))

#             process.wait()
#             if process.returncode == 0:
#                 self.finished.emit(self.output_path)
#             else:
#                 self.error.emit("Error exporting video")
#         except Exception as e:
#             self.error.emit(str(e))

# class VideoEditor(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("AppCutShort")
#         self.setGeometry(100, 100, 1200, 800)
#         self.setStyleSheet("background-color: #2d2d2d; color: white;")

#         # Tạo thư mục tạm và thư mục xuất
#         if not os.path.exists('temp'):
#             os.makedirs('temp')
#         if not os.path.exists('output'):
#             os.makedirs('output')

#         self.video_path = None
#         self.processed_path = None
#         self.subtitles = []  # Danh sách phụ đề: [(start, end, text), ...]
#         self.init_ui()

#     def init_ui(self):
#         # Widget chính
#         central_widget = QWidget()
#         self.setCentralWidget(central_widget)
#         main_layout = QVBoxLayout(central_widget)

#         # Thanh menu trên cùng
#         menu_bar = QHBoxLayout()
#         title_label = QLabel("AppCutShort")
#         title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
#         import_btn = QPushButton("Import")
#         import_btn.setStyleSheet("background-color: #3b82f6; padding: 5px 15px; border-radius: 5px;")
#         import_btn.clicked.connect(self.import_video)
#         export_btn = QPushButton("Export")
#         export_btn.setStyleSheet("background-color: #22c55e; padding: 5px 15px; border-radius: 5px;")
#         export_btn.clicked.connect(self.show_export_dialog)
#         menu_bar.addWidget(title_label)
#         menu_bar.addStretch()
#         menu_bar.addWidget(import_btn)
#         menu_bar.addWidget(export_btn)
#         main_layout.addLayout(menu_bar)

#         # Nội dung chính
#         content_layout = QHBoxLayout()

#         # Preview video
#         self.preview_area = QFrame()
#         self.preview_area.setStyleSheet("background-color: black; border-radius: 10px;")
#         self.preview_area.setFixedWidth(800)
#         self.preview_label = QLabel("No video loaded")
#         self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         self.preview_label.setStyleSheet("color: gray;")
#         preview_layout = QVBoxLayout(self.preview_area)
#         preview_layout.addWidget(self.preview_label)
#         content_layout.addWidget(self.preview_area)

#         # Công cụ chỉnh sửa
#         edit_panel = QFrame()
#         edit_panel.setStyleSheet("background-color: #3d3d3d; border-radius: 10px; padding: 10px;")
#         edit_layout = QVBoxLayout(edit_panel)

#         # Nhập URL
#         url_label = QLabel("YouTube URL")
#         url_label.setStyleSheet("font-weight: bold;")
#         self.url_input = QLineEdit()
#         self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
#         self.url_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
#         load_btn = QPushButton("Load Video")
#         load_btn.setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
#         load_btn.clicked.connect(self.load_video)
#         edit_layout.addWidget(url_label)
#         edit_layout.addWidget(self.url_input)
#         edit_layout.addWidget(load_btn)

#         # Tỷ lệ khung hình
#         ratio_label = QLabel("Aspect Ratio")
#         ratio_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
#         ratio_layout = QHBoxLayout()
#         self.ratio_buttons = {}
#         for ratio in ['9:16', '16:9', '1:1']:
#             btn = QPushButton(ratio)
#             btn.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
#             btn.clicked.connect(lambda checked, r=ratio: self.select_ratio(r))
#             ratio_layout.addWidget(btn)
#             self.ratio_buttons[ratio] = btn
#         self.ratio_buttons['16:9'].setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
#         edit_layout.addWidget(ratio_label)
#         edit_layout.addLayout(ratio_layout)

#         # Font chữ
#         font_label = QLabel("Font")
#         font_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
#         self.font_combo = QComboBox()
#         self.font_combo.addItems(['Arial', 'Roboto', 'Montserrat'])
#         self.font_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
#         edit_layout.addWidget(font_label)
#         edit_layout.addWidget(self.font_combo)

#         # Màu sắc phụ đề
#         color_label = QLabel("Caption Color")
#         color_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
#         self.color_btn = QPushButton("Pick Color")
#         self.color_btn.setStyleSheet("background-color: #ffffff; padding: 5px; border-radius: 5px;")
#         self.color_btn.clicked.connect(self.pick_color)
#         edit_layout.addWidget(color_label)
#         edit_layout.addWidget(self.color_btn)

#         # Nút xử lý
#         process_btn = QPushButton("Process Video")
#         process_btn.setStyleSheet("background-color: #3b82f6; padding: 10px; border-radius: 5px; margin-top: 20px;")
#         process_btn.clicked.connect(self.process_video)
#         edit_layout.addWidget(process_btn)

#         edit_layout.addStretch()
#         content_layout.addWidget(edit_panel)
#         main_layout.addLayout(content_layout)

#         # Timeline
#         timeline_area = QFrame()
#         timeline_area.setStyleSheet("background-color: #3d3d3d; border-radius: 10px;")
#         timeline_area.setFixedHeight(150)
#         timeline_layout = QVBoxLayout(timeline_area)

#         # Bảng phụ đề
#         self.subtitle_table = QTableWidget()
#         self.subtitle_table.setStyleSheet("background-color: #4d4d4d; border: none;")
#         self.subtitle_table.setColumnCount(3)
#         self.subtitle_table.setHorizontalHeaderLabels(['Start', 'End', 'Text'])
#         self.subtitle_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
#         self.subtitle_table.setRowCount(0)
#         timeline_layout.addWidget(self.subtitle_table)

#         # Nút thêm phụ đề
#         add_subtitle_btn = QPushButton("Add Caption")
#         add_subtitle_btn.setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
#         add_subtitle_btn.clicked.connect(self.add_subtitle)
#         timeline_layout.addWidget(add_subtitle_btn)

#         main_layout.addWidget(timeline_area)

#         # Progress bar
#         self.progress_bar = QProgressBar()
#         self.progress_bar.setStyleSheet("margin-top: 10px;")
#         self.progress_bar.setVisible(False)
#         main_layout.addWidget(self.progress_bar)

#     def import_video(self):
#         self.url_input.setFocus()

#     def load_video(self):
#         url = self.url_input.text()
#         if not url:
#             QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
#             return

#         try:
#             yt = YouTube(url)
#             stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
#             if not stream:
#                 QMessageBox.warning(self, "Error", "No suitable video stream found")
#                 return

#             self.video_path = os.path.join('temp', 'input.mp4')
#             stream.download(output_path='temp', filename='input.mp4')
#             self.preview_label.setText("Video loaded. Ready to process.")
#         except Exception as e:
#             QMessageBox.critical(self, "Error", f"Failed to load video: {str(e)}")

#     def select_ratio(self, ratio):
#         for r, btn in self.ratio_buttons.items():
#             btn.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
#         self.ratio_buttons[ratio].setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")

#     def pick_color(self):
#         color = QColorDialog.getColor()
#         if color.isValid():
#             self.color_btn.setStyleSheet(f"background-color: {color.name()}; padding: 5px; border-radius: 5px;")

#     def add_subtitle(self):
#         dialog = QDialog(self)
#         dialog.setWindowTitle("Add Caption")
#         dialog.setStyleSheet("background-color: #3d3d3d; color: white;")
#         layout = QVBoxLayout(dialog)

#         start_label = QLabel("Start Time (HH:MM:SS,mmm)")
#         start_input = QLineEdit("00:00:00,000")
#         start_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
#         layout.addWidget(start_label)
#         layout.addWidget(start_input)

#         end_label = QLabel("End Time (HH:MM:SS,mmm)")
#         end_input = QLineEdit("00:00:05,000")
#         end_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
#         layout.addWidget(end_label)
#         layout.addWidget(end_input)

#         text_label = QLabel("Caption Text")
#         text_input = QTextEdit("Sample Caption")
#         text_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
#         layout.addWidget(text_label)
#         layout.addWidget(text_input)

#         add_btn = QPushButton("Add")
#         add_btn.setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
#         add_btn.clicked.connect(lambda: self.save_subtitle(start_input.text(), end_input.text(), text_input.toPlainText(), dialog))
#         layout.addWidget(add_btn)

#         dialog.exec()

#     def save_subtitle(self, start, end, text, dialog):
#         self.subtitles.append((start, end, text))
#         row = self.subtitle_table.rowCount()
#         self.subtitle_table.setRowCount(row + 1)
#         self.subtitle_table.setItem(row, 0, QTableWidgetItem(start))
#         self.subtitle_table.setItem(row, 1, QTableWidgetItem(end))
#         self.subtitle_table.setItem(row, 2, QTableWidgetItem(text))
#         dialog.accept()

#     def process_video(self):
#         if not self.video_path:
#             QMessageBox.warning(self, "Error", "Please load a video first")
#             return

#         if not self.subtitles:
#             QMessageBox.warning(self, "Error", "Please add at least one caption")
#             return

#         aspect_ratio = [r for r, btn in self.ratio_buttons.items() if "background-color: #3b82f6" in btn.styleSheet()][0]
#         font = self.font_combo.currentText()
#         color = self.color_btn.styleSheet().split('background-color: ')[1].split(';')[0]
#         output_path = os.path.join('temp', 'processed.mp4')

#         self.progress_bar.setVisible(True)
#         self.progress_bar.setValue(0)

#         self.process_thread = ProcessThread(self.video_path, output_path, aspect_ratio, font, color, self.subtitles)
#         self.process_thread.progress.connect(self.update_progress)
#         self.process_thread.finished.connect(self.process_finished)
#         self.process_thread.error.connect(self.show_error)
#         self.process_thread.start()

#     def update_progress(self, value):
#         self.progress_bar.setValue(value)

#     def process_finished(self, output_path):
#         self.progress_bar.setVisible(False)
#         self.processed_path = output_path
#         self.preview_label.setText("Video processed. Ready to export.")
#         QMessageBox.information(self, "Success", "Video processed successfully")

#     def show_error(self, message):
#         self.progress_bar.setVisible(False)
#         QMessageBox.critical(self, "Error", message)

#     def show_export_dialog(self):
#         if not self.processed_path:
#             QMessageBox.warning(self, "Error", "Please process a video first")
#             return

#         dialog = QDialog(self)
#         dialog.setWindowTitle("Export Video")
#         dialog.setStyleSheet("background-color: #3d3d3d; color: white;")
#         layout = QVBoxLayout(dialog)

#         resolution_label = QLabel("Resolution")
#         resolution_label.setStyleSheet("font-weight: bold;")
#         resolution_combo = QComboBox()
#         resolution_combo.addItems(['720p', '1080p', '2K', '4K'])
#         resolution_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
#         layout.addWidget(resolution_label)
#         layout.addWidget(resolution_combo)

#         export_btn = QPushButton("Export")
#         export_btn.setStyleSheet("background-color: #22c55e; padding: 10px; border-radius: 5px; margin-top: 10px;")
#         export_btn.clicked.connect(lambda: self.export_video(resolution_combo.currentText(), dialog))
#         layout.addWidget(export_btn)

#         dialog.exec()

#     def export_video(self, resolution, dialog):
#         output_path = os.path.join('output', f"final-{resolution}.mp4")

#         self.progress_bar.setVisible(True)
#         self.progress_bar.setValue(0)

#         self.export_thread = ExportThread(self.processed_path, output_path, resolution)
#         self.export_thread.progress.connect(self.update_progress)
#         self.export_thread.finished.connect(lambda path: self.export_finished(path, dialog))
#         self.export_thread.error.connect(self.show_error)
#         self.export_thread.start()

#     def export_finished(self, output_path, dialog):
#         self.progress_bar.setVisible(False)
#         dialog.close()
#         QMessageBox.information(self, "Success", f"Video exported successfully at: {output_path}")

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = VideoEditor()
#     window.show()
#     sys.exit(app.exec())

# import sys
# import os
# from PyQt6.QtWidgets import QApplication
# from src.ui.main_window import VideoEditor

# # Tạo thư mục tạm và thư mục xuất nếu chưa tồn tại
# if not os.path.exists('temp'):
#     os.makedirs('temp')
# if not os.path.exists('output'):
#     os.makedirs('output')

import sys
import os
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import VideoEditor

if not os.path.exists('temp'):
    os.makedirs('temp')
if not os.path.exists('output'):
    os.makedirs('output')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoEditor()
    window.show()
    sys.exit(app.exec())