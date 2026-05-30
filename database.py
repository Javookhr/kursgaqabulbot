import sqlite3
from datetime import datetime

DB_NAME = "bot.db"


def get_conn():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            full_name   TEXT,
            phone       TEXT,
            username    TEXT DEFAULT '',
            joined_at   TEXT,
            is_active   INTEGER DEFAULT 1
        )
    """)

    # Kurs haqida ma'lumot (rasm/video/pdf/matn)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS course_info (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT,
            file_id      TEXT,
            caption      TEXT DEFAULT ''
        )
    """)

    # Kurs narxi
    cur.execute("""
        CREATE TABLE IF NOT EXISTS course_price (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT,
            file_id      TEXT,
            caption      TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()


# ─── Foydalanuvchilar ────────────────────────────────────────────────────────

def add_user(telegram_id: int, full_name: str, phone: str, username: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (telegram_id, full_name, phone, username, joined_at, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        ON CONFLICT(telegram_id) DO UPDATE SET
            full_name = excluded.full_name,
            phone     = excluded.phone,
            username  = excluded.username,
            is_active = 1
    """, (telegram_id, full_name, phone, username, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()


def get_user(telegram_id: int):
    """Qaytaradi: (id, telegram_id, full_name, phone, username, joined_at, is_active)"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_all_active_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE is_active = 1")
    rows = cur.fetchall()
    conn.close()
    return rows


def deactivate_user(telegram_id: int):
    """O'quvchini ro'yxatdan o'chiradi (admin 'Bog'lanib bo'ldim' bosganida)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_active = 0 WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()


# ─── Kurs ma'lumoti ──────────────────────────────────────────────────────────

def save_course_info(content_type: str, file_id: str, caption: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM course_info")
    cur.execute(
        "INSERT INTO course_info (content_type, file_id, caption) VALUES (?, ?, ?)",
        (content_type, file_id, caption),
    )
    conn.commit()
    conn.close()


def get_course_info():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, content_type, file_id, caption FROM course_info")
    rows = cur.fetchall()
    conn.close()
    return rows


# ─── Kurs narxi ─────────────────────────────────────────────────────────────

def save_course_price(content_type: str, file_id: str, caption: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM course_price")
    cur.execute(
        "INSERT INTO course_price (content_type, file_id, caption) VALUES (?, ?, ?)",
        (content_type, file_id, caption),
    )
    conn.commit()
    conn.close()


def get_course_price():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, content_type, file_id, caption FROM course_price")
    rows = cur.fetchall()
    conn.close()
    return rows
