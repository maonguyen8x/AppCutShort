from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton

class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter License Key")
        self.setStyleSheet("background-color: #3d3d3d; color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("Please enter your license key:")
        self.key_input = QLineEdit()
        self.key_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px;")
        layout.addWidget(label)
        layout.addWidget(self.key_input)

        submit_btn = QPushButton("Submit")
        submit_btn.setStyleSheet("background-color: #3b82f6; padding: 5px; border-radius: 5px;")
        submit_btn.clicked.connect(self.accept)
        layout.addWidget(submit_btn)

    def get_license_key(self):
        return self.key_input.text()