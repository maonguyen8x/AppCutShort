import sys
import os
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import VideoEditor  # Import from main_windows, not main_window

if not os.path.exists('temp'):
    os.makedirs('temp')
if not os.path.exists('output'):
    os.makedirs('output')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoEditor()
    window.show()
    sys.exit(app.exec())