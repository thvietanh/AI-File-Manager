import sys
from PySide6.QtWidgets import QApplication
from ui.app import AIFileManager

def main():
    app = QApplication(sys.argv)
    window = AIFileManager()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()