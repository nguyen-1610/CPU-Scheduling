"""
main_gui.py – Entry point cho ứng dụng GUI Lab 02.

Chạy:
    python -m src.main_gui
    (Cần quyền sudo để đọc raw FAT32 device trên macOS)
"""

import sys
import signal
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow


def main() -> None:
    # Cho phép Ctrl+C đóng chương trình (SIGINT)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = MainWindow()
    win.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
