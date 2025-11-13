import sqlite3
import os

# Data directories
DATA_DIR = "data"
DOCS_DIR = os.path.join(DATA_DIR, "documents")
TREES_DIR = os.path.join(DATA_DIR, "trees")
DB_PATH = os.path.join(DATA_DIR, "storage.db")


def get_db_connection():
    """Get a database connection"""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)

    # Documents table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            size INTEGER NOT NULL,
            page_count INTEGER,
            status TEXT DEFAULT 'uploaded',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            tree_id INTEGER
        )
    ''')

    # Trees table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            tree_data TEXT NOT NULL,
            num_pages INTEGER,
            num_nodes INTEGER,
            config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doc_id) REFERENCES documents(id)
        )
    ''')

    # Conversations table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            doc_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doc_id) REFERENCES documents(id)
        )
    ''')

    # Messages table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tokens INTEGER,
            cost REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    ''')

    conn.commit()
    conn.close()


def init_storage():
    """Initialize storage directories and database"""
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(TREES_DIR, exist_ok=True)
    init_db()
