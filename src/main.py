import sys
from mainWindow import MainWindow
from PySide6.QtWidgets import QApplication
from config import check_config_json

def main():
    app = QApplication(sys.argv)
    check_config_json()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()