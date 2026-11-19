from process.process_document import process_document
from database.embedded_data import (
    create_chunks_table,
    save_document_chunks
)

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
