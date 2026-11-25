from pathlib import Path

from PySide6.QtCore import QThread, Signal

from function.file_services import get_files
from process.doc_extract import extract, official_extract
from database.data import (
    insert_document,
    insert_official_document
)

class FileThread(QThread):
    progress = Signal(int, int, str)
    error = Signal(str)

    def __init__(self, folder):
        super().__init__()
        self.folder = folder

    def run(self):
        try:
            scanned_files = get_files(self.folder)
            total = len(scanned_files)

            from function.doc_services import index_document

            for current, file in enumerate(scanned_files, 1):
                file_path = Path(file["path"])

                try:
                    # Extract content
                    content = extract(file_path)

                    # Save document
                    document_id = insert_document(
                        file_name=file["name"],
                        file_size=file["size"],
                        file_type=file["extension"],
                        file_path=file_path,
                        content=content
                    )

                    if document_id is not None and content:
                        # Extract official document metadata
                        metadata = official_extract(content)

                        if metadata:
                            insert_official_document(
                                document_id, metadata
                            )

                        # Chunking + Embedding + Save vectors
                        index_document(document_id, content)

                except Exception as e:
                    self.error.emit(
                        f"{file['name']}: {str(e)}"
                    )

                self.progress.emit(
                    current, total, file["name"]
                )

        except Exception as e:
            self.error.emit(str(e))


class SearchThread(QThread):
    result_ready = Signal(object)
    error = Signal(str)

    def __init__(self, files, query, mode, file_type, filters):
        super().__init__()

        self.files = files
        self.query = query
        self.mode = mode
        self.file_type = file_type
        self.filters = filters

    def run(self):
        try:
            from function.search_services import search_documents

            result = search_documents(
                self.files,
                query=self.query,
                mode=self.mode,
                file_type=self.file_type,
                filters=self.filters
            )

            self.result_ready.emit(result)

        except Exception as e:
            self.error.emit(str(e))
