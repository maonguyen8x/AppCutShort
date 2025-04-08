import sys
import os
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow  # Import from main_windows, not main_window

if not os.path.exists('temp'):
    os.makedirs('temp')
if not os.path.exists('output'):
    os.makedirs('output')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())