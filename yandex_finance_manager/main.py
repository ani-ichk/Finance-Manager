import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow
import database


def main():
    database.init_database()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()