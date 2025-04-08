from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt

class ProDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Upgrade to Pro")
        self.setStyleSheet("background-color: #3d3d3d; color: white;")
        self.setMinimumSize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Title
        title_label = QLabel("Unlock Premium Features with Pro")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Plans layout (Monthly and Yearly)
        plans_layout = QHBoxLayout()
        plans_layout.setSpacing(20)

        # Monthly Plan
        monthly_frame = QFrame()
        monthly_frame.setStyleSheet("background-color: #4d4d4d; border-radius: 10px; padding: 15px;")
        monthly_layout = QVBoxLayout(monthly_frame)
        monthly_title = QLabel("Monthly")
        monthly_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        monthly_price = QLabel("$5.9 / month")
        monthly_price.setStyleSheet("font-size: 14px; color: #22c55e; margin-bottom: 10px;")
        monthly_features = QLabel("• No watermark\n"
                                 "• Export videos in 4K\n"
                                 "• Schedule social posts\n"
                                 "• Videos stored forever\n"
                                 "• Manage 6 social media accounts")
        monthly_features.setStyleSheet("font-size: 14px; margin-bottom: 15px;")
        monthly_subscribe_btn = QPushButton("Subscribe")
        monthly_subscribe_btn.setStyleSheet("background-color: #3b82f6; padding: 8px 15px; border-radius: 5px; font-size: 14px;")
        monthly_subscribe_btn.clicked.connect(self.accept)  # Placeholder for subscription logic
        monthly_layout.addWidget(monthly_title)
        monthly_layout.addWidget(monthly_price)
        monthly_layout.addWidget(monthly_features)
        monthly_layout.addWidget(monthly_subscribe_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        plans_layout.addWidget(monthly_frame)

        # Yearly Plan
        yearly_frame = QFrame()
        yearly_frame.setStyleSheet("background-color: #4d4d4d; border-radius: 10px; padding: 15px;")
        yearly_layout = QVBoxLayout(yearly_frame)
        yearly_title = QLabel("Yearly (SAVE 50%)")
        yearly_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        yearly_price = QLabel("$10.9 / month")
        yearly_price.setStyleSheet("font-size: 14px; color: #22c55e; margin-bottom: 10px;")
        yearly_features = QLabel("• Invite team members + $5/mo/seat\n"
                                "• Unlimited viewers\n"
                                "• Brand kit\n"
                                "• Custom fonts\n"
                                "• Manage 20 social media accounts")
        yearly_features.setStyleSheet("font-size: 14px; margin-bottom: 15px;")
        yearly_subscribe_btn = QPushButton("Subscribe")
        yearly_subscribe_btn.clicked.connect(self.accept)  # Placeholder for subscription logic
        yearly_subscribe_btn.setStyleSheet("background-color: #3b82f6; padding: 8px 15px; border-radius: 5px; font-size: 14px;")
        yearly_layout.addWidget(yearly_title)
        yearly_layout.addWidget(yearly_price)
        yearly_layout.addWidget(yearly_features)
        yearly_layout.addWidget(yearly_subscribe_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        plans_layout.addWidget(yearly_frame)

        layout.addLayout(plans_layout)

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #ef4444; padding: 8px 15px; border-radius: 5px; font-size: 14px; margin-top: 20px;")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)