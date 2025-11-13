"""Database initialization and helpers"""
import sqlite3

def init_db():
    """Initialize database tables"""
    conn = sqlite3.connect('data/settings.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            service TEXT PRIMARY KEY,
            encrypted_key TEXT NOT NULL,
            partial_key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS configurations (
            category TEXT PRIMARY KEY,
            settings TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usage_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            queries_count INTEGER DEFAULT 0,
            tokens_used INTEGER DEFAULT 0,
            cost REAL DEFAULT 0.0,
            cache_hits INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def mask_key(key: str) -> str:
    """Mask API key for display (show first 7 and last 4 chars)"""
    if len(key) > 11:
        return f"{key[:7]}...{key[-4:]}"
    return "***"
