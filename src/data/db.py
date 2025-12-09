# src/data/db.py

import sqlite3
from pathlib import Path

# game.db, data klasörünün içinde dursun
DB_PATH = Path(__file__).with_name("game.db")


def get_connection() -> sqlite3.Connection:
    """
    Her repo buradan bağlantı alır.
    row_factory = sqlite3.Row → sütunlara isimle erişebilelim.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Uygulama başlarken bir kere çağrılır.
    Tablolar yoksa oluşturur.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        -- Her kullanıcı için tek satır preferences
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            theme TEXT DEFAULT 'forest',
            music_volume REAL DEFAULT 1.0,
            sfx_volume REAL DEFAULT 1.0,
            music_muted INTEGER DEFAULT 0,
            sfx_muted INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Her oyun için bir satır: skor + kazandı mı kaybetti mi
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            won INTEGER NOT NULL,            -- 1: win, 0: loss
            played_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )

    conn.commit()
    conn.close()


# 🔥 ÖNEMLİ: Bu modül import EDİLİR EDİLMEZ tabloları kur:
print(f"[DB] Using DB file: {DB_PATH}")
init_db()
print("[DB] init_db finished")
