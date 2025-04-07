from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton

class SubtitleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Caption")
        self.setStyleSheet("background-color: #3d3d3d; color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        start_label = QLabel("Start Time (HH:MM:SS,mmm)")
        self.start_input = QLineEdit("00:00:00,000")
        self.start_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        layout.addWidget(start_label)
        layout.addWidget(self.start_input)

        end_label = QLabel("End Time (HH:MM:SS,mmm)")
        self.end_input = QLineEdit("00:00:05,000")
        self.end_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        layout.addWidget(end_label)
        layout.addWidget(self.end_input)

        text_label = QLabel("Caption Text")
        self.text_input = QTextEdit("Sample Caption")
        self.text_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        layout.addWidget(text_label)
        layout.addWidget(self.text_input)

        add_btn = QPushButton("Add")
        add_btn.setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
        add_btn.clicked.connect(self.accept)
        layout.addWidget(add_btn)

    def get_subtitle_data(self):
        return (self.start_input.text(), self.end_input.text(), self.text_input.toPlainText())