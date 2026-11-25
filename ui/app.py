from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QFileDialog,
    QComboBox, QHeaderView, QMessageBox, QSizePolicy,
    QDateEdit, QGroupBox, QFormLayout, QTextEdit, QProgressBar
)
from PySide6.QtCore import QDate

# Services
from function.file_services import open_file
from function.thread import FileThread
from function.doc_services import (
    init_database,
    reset_index,
    load_indexed_files
)
from function.search_services import (
    search_documents,
    has_official_filter,
    warm_up_model
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
        self.semantic_scores = {}
        self.show_semantic_scores = False
        self.semantic_snippets = {}

        self.scaling_factor = 0.8

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(200)
        self.progress_bar.setMaximumWidth(300)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()

        self.statusBar().addPermanentWidget(self.progress_bar)

        # Create database when open app
        init_database()
        reset_index()

        warm_up_model()

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
        self.search_input.setPlaceholderText("Nhập từ khóa...")
        self.search_input.setMinimumHeight(38)
        self.search_input.returnPressed.connect(self.run_search)

        self.search_mode = QComboBox()
        self.search_mode.addItems(["Tên file", "Nội dung"])

        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "Tất cả định dạng", ".pdf", ".docx", ".txt"
        ])
        self.type_filter.currentTextChanged.connect(self.run_search)

        search_button = QPushButton("Tìm kiếm")
        search_button.clicked.connect(self.run_search)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_mode)
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

        clear_button = QPushButton("Xóa bộ lọc")
        clear_button.setFixedSize(110, 32)
        clear_button.clicked.connect(
            self.clear_filters
        )

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

        toolbar.addWidget(choose_button)
        toolbar.addWidget(refresh_button)

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

        # Search result preview
        snippet_label = QLabel("Đoạn nội dung tìm kiếm được")
        snippet_label.setStyleSheet("font-weight: bold;")

        self.snippet_preview = QTextEdit()
        self.snippet_preview.setReadOnly(True)
        self.snippet_preview.setPlaceholderText(
            "Đoạn nội dung phù hợp sẽ hiển thị ở đây..."
        )

        # Extracted document content
        preview_label = QLabel("Nội dung tài liệu trích xuất")
        preview_label.setStyleSheet("font-weight: bold;")

        self.preview_table = QTextEdit()
        self.preview_table.setReadOnly(True)
        self.preview_table.setPlaceholderText(
            "Chọn một file để xem nội dung..."
        )


        self.table.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        self.table.verticalHeader().setDefaultSectionSize(30)

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
        right_layout.addWidget(self.table, 5)

        right_layout.addWidget(snippet_label)
        right_layout.addWidget(self.snippet_preview, 2)

        right_layout.addWidget(preview_label)
        right_layout.addWidget(self.preview_table, 3)

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
            reset_index()
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
        self.semantic_scores.clear()
        self.show_semantic_scores = False

        self.worker = FileThread(self.root_folder)

        self.worker.progress.connect(self.on_loading_progress)
        self.worker.error.connect(
            lambda message: print("Error:", message)
        )
        self.worker.finished.connect(self.on_loading_finished)

        self.worker.start()


        # Auto search at start
        self.run_search()

    # Search

    def read_filters(self):
        def get_date(date_edit):
            if date_edit.date() == date_edit.minimumDate():
                return None

            return date_edit.date().toString("yyyy-MM-dd")

        return {
            "document_number": self.document_number.text().strip() or None,
            "signing_from": get_date(self.signing_from),
            "signing_to": get_date(self.signing_to),
            "effective_from": get_date(self.effective_from),
            "effective_to": get_date(self.effective_to),
            "deadline_from": get_date(self.deadline_from),
            "deadline_to": get_date(self.deadline_to),
        }

    def run_search(self):
        filters = self.read_filters()

        self.show_official_info = has_official_filter(filters)

        mode = (
            "content"
            if self.search_mode.currentText() == "Nội dung"
            else "name"
        )

        file_type = self.type_filter.currentText()
        if file_type == "Tất cả định dạng":
            file_type = None

        result = search_documents(
            self.files,
            query=self.search_input.text(),
            mode=mode,
            file_type=file_type,
            filters=filters
        )

        self.semantic_scores = result.scores
        self.semantic_snippets = result.snippets
        self.show_semantic_scores = result.semantic
        self.display_results(result.files)

    # Display results

    def display_results(self, results):
        self.displayed_files = results

        headers = [
            "Tên file",
            "Định dạng",
            "Kích thước",
            "Đường dẫn"
        ]

        if self.show_semantic_scores:
            headers.extend(["Điểm"])

        if self.show_official_info:
            headers.extend([
                "Số công văn",
                "Ngày ký",
                "Ngày hiệu lực",
                "Deadline"
            ])

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

        score_column = 4 if self.show_semantic_scores else None
        if score_column is not None:
            header.setSectionResizeMode(
                score_column, QHeaderView.ResizeMode.ResizeToContents
            )

        if self.show_official_info:
            official_start = 6 if self.show_semantic_scores else 4
            for col in range(official_start, official_start + 4):
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

            if self.show_semantic_scores:
                file_id = file["id"]
                score = self.semantic_scores.get(file_id)
                snippet = self.semantic_snippets.get(file_id, "")
                values.extend([
                    "" if score is None else f"{float(score):.3f}",
                    snippet
                ])

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
            self.snippet_preview.clear()
            self.preview_table.clear()
            return

        row = selected_file[0].row()

        if 0 <= row < len(self.displayed_files):
            file = self.displayed_files[row]
            file_id = file["id"]

            snippet = self.semantic_snippets.get(file_id, "")
            content = file.get("content") or ""

            self.snippet_preview.setPlainText(
                snippet if snippet else "Không có đoạn nội dung phù hợp."
            )

            self.preview_table.setPlainText(
                content if content else "Không tìm thấy nội dung tài liệu."
            )

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
        self.semantic_scores.clear()
        self.show_semantic_scores = False
        self.document_number.clear()

        date_edits = [
            self.signing_from, self.signing_to,
            self.effective_from, self.effective_to,
            self.deadline_from, self.deadline_to
        ]

        for date_edit in date_edits:
            date_edit.setDate(date_edit.minimumDate())

        self.run_search()

    # Refresh files

    def refresh_files(self):
        if not self.root_folder:
            return

        reset_index()
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
        self.files, self.official_metadata = load_indexed_files(
            self.root_folder
        )

        self.run_search()

        # Done

        self.progress_bar.hide()
        self.statusBar().showMessage(
            "Đã hoàn tất xử lý tài liệu!", 5000
        )

        self.worker.deleteLater()
        self.worker = None