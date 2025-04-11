from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox

class LicenseKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter License Key")
        self.setStyleSheet("background-color: #2d2d2d; color: white;")
        self.setFixedSize(300, 150)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)
        self.key_input = QLineEdit()
        self.key_input.setStyleSheet("background-color: #3d3d3d; padding: 5px; border-radius: 5px; font-size: 14px; color: white;")
        layout.addRow("License Key:", self.key_input)

        button_layout = QHBoxLayout()
        activate_btn = QPushButton("Activate")
        activate_btn.setStyleSheet("background-color: #3b82f6; padding: 5px 10px; border-radius: 5px; font-size: 14px;")
        activate_btn.clicked.connect(self.activate_key)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #ef4444; padding: 5px 10px; border-radius: 5px; font-size: 14px;")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(activate_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)

    def activate_key(self):
        key = self.key_input.text().strip()
        if key:
            QMessageBox.information(self, "Success", "License key activated successfully!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Please enter a valid license key.")