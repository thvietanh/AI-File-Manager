import sqlite3
import numpy as np

from database.data import create_connection

def create_chunks_table():
    connection = create_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding BLOB NOT NULL,

            FOREIGN KEY (document_id)
                REFERENCES documents(id)
                ON DELETE CASCADE,

            UNIQUE(document_id, chunk_index)
        )
    """)

    connection.commit()
    connection.close()


def save_document_chunks(document_id, chunks):
    connection = create_connection()

    try:
        # Delete old chunks
        connection.execute(
            "DELETE FROM document_chunks WHERE document_id = ?",
            (document_id,)
        )

        data = []

        for chunk in chunks:
            vector = np.asarray(
                chunk["embedding"],
                dtype=np.float32
            )

            data.append((
                document_id,
                chunk["chunk_index"],
                chunk["content"],
                vector.tobytes()
            ))

        connection.executemany("""
            INSERT INTO document_chunks
            (document_id, chunk_index, content, embedding)
            VALUES (?, ?, ?, ?)
        """, data)

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_document_chunks(document_id):
    connection = create_connection()

    rows = connection.execute("""
        SELECT chunk_index, content, embedding
        FROM document_chunks
        WHERE document_id = ?
        ORDER BY chunk_index
    """, (document_id,)).fetchall()

    connection.close()

    results = []

    for row in rows:
        vector = np.frombuffer(
            row[2],
            dtype=np.float32
        )

        results.append({
            "chunk_index": row[0],
            "content": row[1],
            "embedding": vector
        })

    return results

def get_all_chunks():
    connection = create_connection()

    rows = connection.execute("""
        SELECT document_id, chunk_index, content, embedding
        FROM document_chunks
    """).fetchall()

    connection.close()
    return rows