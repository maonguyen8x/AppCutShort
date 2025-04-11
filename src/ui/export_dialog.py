from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel, QComboBox

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Video")
        self.setStyleSheet("background-color: #2d2d2d; color: white;")
        self.setFixedSize(400, 250)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.output_path = QLineEdit()
        self.output_path.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        self.output_path.setPlaceholderText("Select output path...")

        browse_btn = QPushButton("Browse")
        browse_btn.setStyleSheet("background-color: #3d3d3d; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        browse_btn.clicked.connect(self.browse_output_path)

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Output Path:"))
        path_layout.addWidget(self.output_path)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("Resolution:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["480p", "720p", "1080p", "2K", "4K"])
        self.resolution_combo.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        layout.addLayout(resolution_layout)

        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet("background-color: #22c55e; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        export_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #ef4444; padding: 5px 10px; border-radius: 5px; font-size: 14px; color: white;")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(export_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def browse_output_path(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Select Output Path", "", "Video Files (*.mp4)")
        if file_path:
            self.output_path.setText(file_path)