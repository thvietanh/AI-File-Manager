import os
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QFileDialog,
    QComboBox, QHeaderView, QMessageBox, QSizePolicy,
    QDateEdit, QGroupBox, QFormLayout, QTextEdit, QProgressBar
)
from PySide6.QtCore import QDate

# Services
from function.file_services import get_files, open_file
from function.thread import FileThread
from function.search_services import semantic_search

# Process
from process.doc_extract import extract, official_extract

# Database
from database.data import (
    create_table,
    insert_document,
    insert_official_document,
    get_official_document,
    get_documents,
    clear_database,
    get_filtered_official_documents
)

from database.embedded_data import (
    create_chunks_table,
    save_document_chunks,
    get_document_chunks
)

class AIFileManager(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI File Manager")
        self.root_folder = ""
        self.files = []

        # Thread
        self.worker = None

        # Display mode
        self.show_official_info = False
        self.displayed_files = []
        self.official_metadata = {}

        self.scaling_factor = 0.8

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setMaximumWidth(300)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()

        self.statusBar().addPermanentWidget(self.progress_bar)

        # Create database when open app

        create_table()
        create_chunks_table()

        self.setup_ui()
        self.setup_window_size()

    # Window size

    def setup_window_size(self):
        screen = QApplication.primaryScreen()
        geometry = screen.availableGeometry()

        width = int(geometry.width() * self.scaling_factor)
        height = int(geometry.height() * self.scaling_factor)

        self.setMinimumSize(900, 600)
        self.resize(width, height)

        x = geometry.x() + (geometry.width() - width) // 2
        y = geometry.y() + (geometry.height() - height) // 2

        self.move(x, y)

    # Setup UI

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

        # Main content: Left + Right
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # LEFT PANEL

        left_panel = QWidget()
        left_panel.setFixedWidth(320)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        # Search area
        search_group = QGroupBox("Tìm kiếm")
        search_layout = QVBoxLayout(search_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Nhập tên file hoặc nội dung..."
        )
        self.search_input.setMinimumHeight(38)
        self.search_input.returnPressed.connect(
            self.search_files
        )

        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "Tất cả định dạng", ".pdf", ".docx", ".txt"
        ])
        self.type_filter.currentTextChanged.connect(
            self.search_files
        )

        search_button = QPushButton("Tìm kiếm")
        search_button.clicked.connect(self.search_files)

        semantic_button = QPushButton("Tìm theo nội dung")
        semantic_button.clicked.connect(self.semantic_search_files)
        search_layout.addWidget(semantic_button)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.type_filter)
        search_layout.addWidget(search_button)

        left_layout.addWidget(search_group)

        # Document filters
        filter_group = QGroupBox("Bộ lọc công văn")
        filter_layout = QFormLayout(filter_group)

        filter_layout.setContentsMargins(8, 8, 8, 8)
        filter_layout.setHorizontalSpacing(5)
        filter_layout.setVerticalSpacing(8)
        filter_layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        self.document_number = QLineEdit()
        self.document_number.setPlaceholderText(
            "Số công văn..."
        )

        # Date filters
        self.signing_from = QDateEdit()
        self.signing_to = QDateEdit()

        self.effective_from = QDateEdit()
        self.effective_to = QDateEdit()

        self.deadline_from = QDateEdit()
        self.deadline_to = QDateEdit()

        date_edits = [
            self.signing_from, self.signing_to,
            self.effective_from, self.effective_to,
            self.deadline_from, self.deadline_to
        ]

        for date_edit in date_edits:
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("dd/MM/yyyy")
            date_edit.setMinimumDate(QDate(1900, 1, 1))
            date_edit.setMaximumDate(QDate(2100, 12, 31))

            date_edit.setSpecialValueText(" ")
            date_edit.setDate(date_edit.minimumDate())

            date_edit.setStyleSheet("""
                QDateEdit {
                    font-size: 11px;
                    padding: 3px;
                }
            """)

        filter_layout.addRow(
            "Số công văn:",
            self.document_number
        )

        filter_layout.addRow(
            "Ngày ký:",
            self.create_date_range(
                self.signing_from, self.signing_to
            )
        )

        filter_layout.addRow(
            "Ngày hiệu lực:",
            self.create_date_range(
                self.effective_from, self.effective_to
            )
        )

        filter_layout.addRow(
            "Deadline:",
            self.create_date_range(
                self.deadline_from, self.deadline_to
            )
        )

        # Filter buttons
        filter_area = QHBoxLayout()
        filter_area.setSpacing(8)

        filter_button = QPushButton("Lọc công văn")
        filter_button.setFixedSize(110, 32)
        filter_button.clicked.connect(
            self.filter_documents
        )

        clear_button = QPushButton("Xóa bộ lọc")
        clear_button.setFixedSize(110, 32)
        clear_button.clicked.connect(
            self.clear_filters
        )

        filter_area.addWidget(filter_button)
        filter_area.addWidget(clear_button)
        filter_area.addStretch()

        filter_layout.addRow(filter_area)

        left_layout.addWidget(filter_group)

        # Toolbar
        toolbar_group = QGroupBox("Thao tác")
        toolbar = QVBoxLayout(toolbar_group)

        choose_button = QPushButton("Chọn thư mục")
        choose_button.clicked.connect(self.choose_folder)

        refresh_button = QPushButton("Làm mới")
        refresh_button.clicked.connect(self.refresh_files)

        self.mode_button = QPushButton(
            "Hiện thông tin công văn"
        )
        self.mode_button.clicked.connect(
            self.toggle_document_mode
        )

        open_button = QPushButton("Mở file")
        open_button.clicked.connect(
            self.open_selected_file
        )

        toolbar.addWidget(choose_button)
        toolbar.addWidget(refresh_button)
        toolbar.addWidget(self.mode_button)
        toolbar.addWidget(open_button)

        left_layout.addWidget(toolbar_group)
        left_layout.addStretch()

        # RIGHT PANEL

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        result_label = QLabel("Danh sách tài liệu")
        result_label.setStyleSheet(
            "font-size: 17px; font-weight: bold;"
        )

        right_layout.addWidget(result_label)

        # File table
        self.table = QTableWidget()
        self.table.setColumnCount(4)

        self.table.setHorizontalHeaderLabels([
            "Tên file",
            "Định dạng",
            "Kích thước",
            "Đường dẫn"
        ])

        # Preview tab

        preview_label = QLabel("Nội dung trích xuất")
        preview_label.setStyleSheet("QLabel {font-weight: bold;}")
        self.preview_table = QTextEdit()
        self.preview_table.setReadOnly(True)
        self.preview_table.setPlaceholderText("Chọn 1 file để xem trước nội dung...")


        self.table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        self.table.verticalHeader().setDefaultSectionSize(60)

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

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.doubleClicked.connect(
            self.open_selected_file
        )

        self.table.itemSelectionChanged.connect(self.preview_selected_file)

        # Add table to right layout
        right_layout.addWidget(self.table, 2)
        right_layout.addWidget(preview_label)
        right_layout.addWidget(self.preview_table, 1)

        # Status
        self.status_label = QLabel("Sẵn sàng")
        self.status_label.setStyleSheet("color: gray;")

        right_layout.addWidget(self.status_label)

        # Combine panels
        content_layout.addWidget(left_panel)
        content_layout.addWidget(right_panel, 1)

        main_layout.addLayout(content_layout, 1)

        # Style

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }

            QGroupBox {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }

            QLineEdit, QComboBox, QDateEdit {
                background-color: white;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 6px;
            }

            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
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

    # Widget for date range selection

    def create_date_range(self, date_from, date_to):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        date_from.setMinimumWidth(0)
        date_to.setMinimumWidth(0)

        date_from.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        date_to.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )

        layout.addWidget(date_from, 1)
        layout.addWidget(QLabel("Đến"))
        layout.addWidget(date_to, 1)

        widget = QWidget()
        widget.setLayout(layout)

        return widget

    # Folder selection

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục"
        )

        if folder:
            if self.worker is not None and self.worker.isRunning(): return
            clear_database()
            self.root_folder = folder
            self.folder_label.setText(folder)
            self.load_files()

    # Load files

    def load_files(self):
        if not self.root_folder:
            return

        if self.worker is not None and self.worker.isRunning():
            return

        self.files.clear()
        self.official_metadata.clear()

        self.worker = FileThread(self.root_folder)

        self.worker.progress.connect(self.on_loading_progress)
        self.worker.error.connect(
            lambda message: print("Error:", message)
        )
        self.worker.finished.connect(self.on_loading_finished)

        self.worker.start()


        # Auto search at start
        self.search_files()

    # Search files

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

    def semantic_search_files(self):
        query = self.search_input.text().strip()
        if not query:
            return

        hits = semantic_search(query, top_k=20)

        files_by_id = {f["id"]: f for f in self.files}
        results = [
            files_by_id[h["document_id"]]
            for h in hits
            if h["document_id"] in files_by_id
        ]

        self.display_results(results)

    # Display results

    def display_results(self, results):
        self.displayed_files = results

        if self.show_official_info:
            headers = [
                "Tên file",
                "Định dạng",
                "Kích thước",
                "Đường dẫn",
                "Số công văn",
                "Ngày ký",
                "Ngày hiệu lực",
                "Deadline"
            ]
        else:
            headers = [
                "Tên file",
                "Định dạng",
                "Kích thước",
                "Đường dẫn"
            ]

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

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

        if self.show_official_info:
            for col in range(4, 8):
                header.setSectionResizeMode(
                    col, QHeaderView.ResizeMode.ResizeToContents
                )

        self.table.setRowCount(len(results))

        for row, file in enumerate(results):
            size_mb = file["size"] / (1024 * 1024)

            values = [
                file["name"],
                file["extension"],
                f"{size_mb:.2f} MB",
                file["path"]
            ]

            if self.show_official_info:
                metadata = self.official_metadata.get(
                    file["id"], {}
                )

                values.extend([
                    metadata.get("document_number") or "",
                    metadata.get("signing_date") or "",
                    metadata.get("effective_date") or "",
                    metadata.get("deadline_date") or ""
                ])

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(str(value))
                self.table.setItem(row, col, item)

        self.status_label.setText(
            f"Tìm thấy {len(results)} tài liệu"
        )

    # Preview selected file
    def preview_selected_file(self):
        selected_file = self.table.selectedItems()
        if not selected_file:
            self.preview_table.clear()
            return

        row = selected_file[0].row()
        file_path = self.table.item(row, 3).text()
        documents = get_documents()

        for doc in documents:
            if doc[4] == file_path:
                content = doc[5]
                self.preview_table.setPlainText(content)
                return

        self.preview_table.setPlainText("Không tìm thấy nội dung file")

    # Toggle display mode

    def toggle_document_mode(self):
        self.show_official_info = not self.show_official_info

        if self.show_official_info:
            self.mode_button.setText(
                "Ẩn thông tin công văn"
            )
        else:
            self.mode_button.setText(
                "Hiện thông tin công văn"
            )

        self.display_results(self.displayed_files)

    # Open selected file

    def open_selected_file(self):
        row = self.table.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "Thông báo",
                "Hãy chọn một file."
            )
            return

        file_path = self.table.item(row, 3).text()

        try:
            open_file(file_path)
        except OSError as error:
            QMessageBox.warning(
                self,
                "Lỗi",
                f"Không thể mở file:\n{error}"
            )

    # Filters

    def clear_filters(self):
        self.document_number.clear()

        date_edits = [
            self.signing_from, self.signing_to,
            self.effective_from, self.effective_to,
            self.deadline_from, self.deadline_to
        ]

        for date_edit in date_edits:
            date_edit.setDate(date_edit.minimumDate())

        self.search_files()

    def filter_documents(self):

        document_number = self.document_number.text().strip()

        def get_date(date_edit):
            if date_edit.date() == date_edit.minimumDate():
                return None

            return date_edit.date().toString("yyyy-MM-dd")

        results = get_filtered_official_documents(
            document_number=document_number or None,

            signing_from=get_date(self.signing_from),
            signing_to=get_date(self.signing_to),

            effective_from=get_date(self.effective_from),
            effective_to=get_date(self.effective_to),

            deadline_from=get_date(self.deadline_from),
            deadline_to=get_date(self.deadline_to)
        )

        filtered_files = []

        keyword = self.search_input.text().strip().lower()
        file_type = self.type_filter.currentText()

        for doc in results:
            (
                document_id,
                name,
                size,
                extension,
                path,
                content,
                created_at
            ) = doc

            if keyword and keyword not in name.lower():
                continue

            if (
                file_type != "Tất cả định dạng"
                and extension != file_type
            ):
                continue

            filtered_files.append({
                "id": document_id,
                "name": name,
                "size": size,
                "extension": extension,
                "path": path,
                "content": content,
                "created_at": created_at
            })

        self.display_results(filtered_files)

    # Refresh files

    def refresh_files(self):
        if not self.root_folder:
            return

        clear_database()
        self.load_files()


    # File thread function idk
    def on_loading_progress(self, current, total, file_name):
        self.progress_bar.show()

        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)

        self.progress_bar.setFormat(
            f"{current}/{total} files"
        )

        self.statusBar().showMessage(
            f"Đang xử lý: {file_name}"
        )

    def on_loading_finished(self):
        documents = get_documents()

        official_documents = get_official_document()

        self.official_metadata = {}

        for doc in official_documents:
            self.official_metadata[doc[0]] = {
                "document_number": doc[6],
                "signing_date": doc[7],
                "effective_date": doc[8],
                "deadline_date": doc[9]
            }

        root_path = os.path.normcase(
            os.path.abspath(self.root_folder)
        )

        for doc in documents:
            (
                document_id,
                file_name,
                file_size,
                file_type,
                file_path,
                content,
                created_at
            ) = doc

            absolute_path = os.path.normcase(
                os.path.abspath(file_path)
            )

            if (
                os.path.commonpath([absolute_path, root_path])
                == root_path
            ):
                self.files.append({
                    "id": document_id,
                    "name": file_name,
                    "size": file_size,
                    "extension": file_type,
                    "path": file_path,
                    "content": content,
                    "created_at": created_at
                })

        self.search_files()

        # Done

        self.progress_bar.hide()
        self.statusBar().showMessage(
            "Đã hoàn tất xử lý tài liệu!", 5000
        )

        self.worker.deleteLater()
        self.worker = None

