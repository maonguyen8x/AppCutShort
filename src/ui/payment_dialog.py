from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
import webbrowser

class PaymentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Payment Options")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #2d2d2d; color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        # Payment options label
        label = QLabel("Select a Payment Method")
        label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(label)

        # Payment buttons
        paypal_btn = QPushButton("PayPal")
        paypal_btn.setStyleSheet("background-color: #0070ba; padding: 8px 20px; border-radius: 5px; font-size: 14px;")
        paypal_btn.clicked.connect(self.open_paypal)
        layout.addWidget(paypal_btn)

        visa_btn = QPushButton("Visa")
        visa_btn.setStyleSheet("background-color: #1a1f71; padding: 8px 20px; border-radius: 5px; font-size: 14px;")
        visa_btn.clicked.connect(self.open_visa)
        layout.addWidget(visa_btn)

        mastercard_btn = QPushButton("MasterCard")
        mastercard_btn.setStyleSheet("background-color: #cc0000; padding: 8px 20px; border-radius: 5px; font-size: 14px;")
        mastercard_btn.clicked.connect(self.open_mastercard)
        layout.addWidget(mastercard_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #ef4444; padding: 8px 20px; border-radius: 5px; font-size: 14px;")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def open_paypal(self):
        # Placeholder: Open PayPal payment page (requires actual PayPal API integration)
        webbrowser.open("https://www.paypal.com")
        self.close()

    def open_visa(self):
        # Placeholder: Open Visa payment page (requires actual payment gateway integration)
        webbrowser.open("https://www.visa.com")
        self.close()

    def open_mastercard(self):
        # Placeholder: Open MasterCard payment page (requires actual payment gateway integration)
        webbrowser.open("https://www.mastercard.com")
        self.close()