import os

from process.process_document import process_document
from database.data import (
    create_table,
    clear_database,
    get_documents,
    get_official_document
)
from database.embedded_data import (
    create_chunks_table,
    save_document_chunks
)


def init_database():
    create_table()
    create_chunks_table()


def reset_index():
    clear_database()


def index_document(document_id, content):
    if not content or not content.strip():
        return False

    # Create chunks
    create_chunks_table()

    # Chunking + Embedding
    chunks = process_document(content)

    if not chunks:
        return False

    # Save to SQLite
    save_document_chunks(document_id, chunks)

    return True


def load_indexed_files(root_folder):
    root_path = os.path.normcase(os.path.abspath(root_folder))

    official_metadata = {}
    for (
        document_id,
        _name,
        _size,
        _type,
        _path,
        _content,
        document_number,
        signing_date,
        effective_date,
        deadline_date
    ) in get_official_document():
        official_metadata[document_id] = {
            "document_number": document_number,
            "signing_date": signing_date,
            "effective_date": effective_date,
            "deadline_date": deadline_date
        }

    files = []
    for (
        document_id,
        file_name,
        file_size,
        file_type,
        file_path,
        content,
        created_at
    ) in get_documents():
        absolute_path = os.path.normcase(os.path.abspath(file_path))

        try:
            inside_root = (
                os.path.commonpath([absolute_path, root_path]) == root_path
            )
        except ValueError:  # khác ổ đĩa (Windows)
            inside_root = False

        if inside_root:
            files.append({
                "id": document_id,
                "name": file_name,
                "size": file_size,
                "extension": file_type,
                "path": file_path,
                "content": content,
                "created_at": created_at
            })

    return files, official_metadata