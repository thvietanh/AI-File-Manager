import os
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QFileDialog,
    QComboBox, QHeaderView, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt


class AIFileManager(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI File Manager")
        self.root_folder = ""
        self.files = []

        self.scaling_factor = 0.7

        self.setup_ui()
        self.setup_window_size()

    def setup_window_size(self):
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()

        width = int(geometry.width() * self.scaling_factor)
        height = int(geometry.height() * self.scaling_factor)

        self.setFixedSize(width, height)

        x = geometry.x() + (geometry.width() - width) // 2
        y = geometry.y() + (geometry.height() - height) // 2

        self.move(x, y)

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Header
        header = QHBoxLayout()

        title = QLabel("AI File Manager")
        title.setStyleSheet(
            "font-size: 26px; font-weight: bold;"
        )

        self.folder_label = QLabel("Chưa chọn thư mục")
        self.folder_label.setStyleSheet("color: gray;")
        self.folder_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.folder_label)

        main_layout.addLayout(header)

        # Search area
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Nhập tên file hoặc nội dung cần tìm..."
        )
        self.search_input.setMinimumHeight(40)
        self.search_input.returnPressed.connect(
            self.search_files
        )

        search_button = QPushButton("Tìm kiếm")
        search_button.clicked.connect(self.search_files)

        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "Tất cả định dạng", ".pdf", ".docx", ".txt"
        ])
        self.type_filter.currentTextChanged.connect(
            self.search_files
        )

        search_layout.addWidget(self.search_input, 4)
        search_layout.addWidget(self.type_filter, 1)
        search_layout.addWidget(search_button)

        main_layout.addLayout(search_layout)

        # Toolbar
        toolbar = QHBoxLayout()

        choose_button = QPushButton("Chọn thư mục")
        choose_button.clicked.connect(self.choose_folder)

        refresh_button = QPushButton("Làm mới")
        refresh_button.clicked.connect(self.load_files)

        open_button = QPushButton("Mở file")
        open_button.clicked.connect(self.open_selected_file)

        toolbar.addWidget(choose_button)
        toolbar.addWidget(refresh_button)
        toolbar.addStretch()
        toolbar.addWidget(open_button)

        main_layout.addLayout(toolbar)

        # Results
        result_label = QLabel("Danh sách tài liệu")
        result_label.setStyleSheet(
            "font-size: 17px; font-weight: bold;"
        )
        main_layout.addWidget(result_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Tên file", "Định dạng", "Kích thước", "Đường dẫn"
        ])

        # Lock row height
        self.table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        self.table.verticalHeader().setDefaultSectionSize(30)

        # Auto-resize columns
        header = self.table.horizontalHeader()

        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.doubleClicked.connect(
            self.open_selected_file
        )

        main_layout.addWidget(self.table, 1)

        # Status
        self.status_label = QLabel("Sẵn sàng")
        self.status_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.status_label)

        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }

            QLineEdit, QComboBox {
                background-color: white;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 8px;
            }

            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
            }

            QPushButton:hover {
                background-color: #1d4ed8;
            }

            QTableWidget {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                gridline-color: #eeeeee;
            }

            QHeaderView::section {
                background-color: #e9edf5;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục"
        )

        if folder:
            self.root_folder = folder
            self.folder_label.setText(folder)
            self.load_files()

    def load_files(self):
        if not self.root_folder:
            return

        self.files.clear()

        for root, dirs, filenames in os.walk(self.root_folder):
            for filename in filenames:
                path = Path(root) / filename

                try:
                    self.files.append({
                        "name": filename,
                        "extension": path.suffix.lower(),
                        "size": path.stat().st_size,
                        "path": str(path)
                    })
                except OSError:
                    continue

        self.search_files()

    def search_files(self):
        keyword = self.search_input.text().strip().lower()
        file_type = self.type_filter.currentText()

        results = []

        for file in self.files:
            if keyword and keyword not in file["name"].lower():
                continue

            if file_type != "Tất cả định dạng":
                if file["extension"] != file_type:
                    continue

            results.append(file)

        self.display_results(results)

    def display_results(self, results):
        self.table.setRowCount(len(results))

        for row, file in enumerate(results):
            size_mb = file["size"] / (1024 * 1024)

            values = [
                file["name"],
                file["extension"],
                f"{size_mb:.2f} MB",
                file["path"]
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.table.setItem(row, col, item)

        self.status_label.setText(
            f"Tìm thấy {len(results)} tài liệu"
        )

    def open_selected_file(self):
        row = self.table.currentRow()

        if row < 0:
            QMessageBox.information(
                self, "Thông báo", "Hãy chọn một file."
            )
            return

        file_path = self.table.item(row, 3).text()

        try:
            os.startfile(file_path)
        except OSError as error:
            QMessageBox.warning(
                self, "Lỗi", f"Không thể mở file:\n{error}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = AIFileManager()
    window.show()

    sys.exit(app.exec())
