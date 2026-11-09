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
                file_path TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Official documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS official_documents (
                document_id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_number TEXT,
                signing_date TEXT,
                effective_date TEXT,
                deadline_date TEXT,
                
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        ''')

        # Indexes for performance optimization
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_file_name ON official_documents(file_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_signing_date ON official_documents(signing_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_effective_date ON official_documents(effective_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deadline_date ON official_documents(deadline_date)')

        connection.commit()

    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

    finally:
        connection.close()


