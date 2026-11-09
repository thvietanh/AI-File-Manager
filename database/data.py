import sqlite3
from pathlib import Path

# Database file path
DATABASE_PATH = Path(__file__).parent / "database.db"

# Create a connection 
def create_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
    return connection

def create_table():
    connection = create_connection()
    try:
        cursor = connection.cursor()

        # Normal documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_type TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Official documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS official_documents (
                document_id INTEGER PRIMARY KEY,
                document_number TEXT,
                signing_date TEXT,
                effective_date TEXT,
                deadline_date TEXT,
                
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        ''')

        # Indexes for performance optimization
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_name ON documents(file_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_type ON documents(file_type)')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_document_number ON official_documents(document_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_signing_date ON official_documents(signing_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_effective_date ON official_documents(effective_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deadline_date ON official_documents(deadline_date)')

        connection.commit()

    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

    finally:
        connection.close()

def insert_document(file_name, file_size, file_type, file_path, content=None):
    connection = create_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO documents (
                file_name,
                file_size,
                file_type,
                file_path,
                content
            )
            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(file_path) DO UPDATE SET
                file_name = excluded.file_name,
                file_size = excluded.file_size,
                file_type = excluded.file_type,
                content = excluded.content
        """, (
            file_name,
            file_size,
            file_type,
            str(file_path),
            content
        ))

        connection.commit()

        cursor.execute(
            "SELECT id FROM documents WHERE file_path = ?",
            (str(file_path),)
        )

        return cursor.fetchone()[0]

    except sqlite3.Error as e:
        print(f"Error inserting document: {e}")
        return None

    finally:
        connection.close()

def get_documents():
    connection = create_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                file_name,
                file_size,
                file_type,
                file_path,
                content,
                created_at
            FROM documents
            ORDER BY created_at DESC
        """)

        documents = cursor.fetchall()
        return documents

    except sqlite3.Error as e:
        print(f"Error getting documents: {e}")
        return []

    finally:
        connection.close()

def delete_document(document_id):
    connection = create_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM documents WHERE id = ?",
            (document_id,)
        )

        connection.commit()
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        print(f"Error deleting document: {e}")
        return False

    finally:
        connection.close()

def update_document(document_id, file_name, file_size, file_type, file_path, content=None):
    connection = create_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE documents
            SET
                file_name = ?,
                file_size = ?,
                file_type = ?,
                file_path = ?,
                content = ?
            WHERE id = ?
        """, (
            file_name,
            file_size,
            file_type,
            str(file_path),
            content,
            document_id
        ))

        connection.commit()

        return cursor.rowcount > 0

    except sqlite3.Error as e:
        print(f"Error updating document: {e}")
        return False

    finally:
        connection.close()

