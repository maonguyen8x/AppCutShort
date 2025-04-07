from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
from src.processing.export_thread import ExportThread

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Export Video")
        self.setStyleSheet("background-color: #3d3d3d; color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        resolution_label = QLabel("Resolution")
        resolution_label.setStyleSheet("font-weight: bold;")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(['720p', '1080p', '2K', '4K'])
        self.resolution_combo.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        layout.addWidget(resolution_label)
        layout.addWidget(self.resolution_combo)

        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("background-color: #22c55e; padding: 10px; border-radius: 5px; margin-top: 10px;")
        export_btn.clicked.connect(self.export_video)
        layout.addWidget(export_btn)

    def export_video(self):
        resolution = self.resolution_combo.currentText()
        output_path = f"output/final-{resolution}.mp4"

        self.parent.progress_bar.setVisible(True)
        self.parent.progress_bar.setValue(0)

        self.export_thread = ExportThread(self.parent.processed_path, output_path, resolution)
        self.export_thread.progress.connect(self.parent.update_progress)
        self.export_thread.finished.connect(lambda path: self.parent.export_finished(path, self))
        self.export_thread.error.connect(self.parent.show_error)
        self.export_thread.start()