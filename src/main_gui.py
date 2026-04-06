"""
main_gui.py – Entry point cho ứng dụng GUI Lab 02.

Chạy:
    python -m src.main_gui
    (cần quyền Administrator trên Windows để đọc raw FAT32 device)
"""

import sys
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    # Style nhẹ cho toàn app
    app.setStyle("Fusion")

    win = MainWindow()
    win.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
