from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from src.ui.payment_dialog import PaymentDialog

class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter License Key")
        self.setFixedSize(400, 200)
        self.setStyleSheet("background-color: #2d2d2d; color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        # License key input
        label = QLabel("Enter your license key:")
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self.key_input.setStyleSheet("background-color: #4d4d4d; padding: 5px; border-radius: 5px; font-size: 14px;")
        layout.addWidget(label)
        layout.addWidget(self.key_input)

        # Buttons
        button_layout = QHBoxLayout()
        submit_btn = QPushButton("Submit")
        submit_btn.setStyleSheet("background-color: #3b82f6; padding: 8px 15px; border-radius: 5px; font-size: 14px;")
        submit_btn.clicked.connect(self.accept)
        subscribe_btn = QPushButton("Subscribe")
        subscribe_btn.setStyleSheet("background-color: #22c55e; padding: 8px 15px; border-radius: 5px; font-size: 14px;")
        subscribe_btn.clicked.connect(self.show_payment_dialog)
        button_layout.addWidget(submit_btn)
        button_layout.addWidget(subscribe_btn)
        layout.addLayout(button_layout)

    def get_license_key(self):
        return self.key_input.text()

    def show_payment_dialog(self):
        """
        Show the payment dialog when the Subscribe button is clicked.
        """
        payment_dialog = PaymentDialog(self)
        payment_dialog.exec()