import sqlite3
from typing import List, Optional
from models import User, Category

DB_PATH = "planpal.sqlite3"

class Storage:
    """Small wrapper around sqlite for now"""
    def __init__(self, path: str = DB_PATH):
        # Connect and enable dict-like row access
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """Create schema"""
        cur = self.conn.cursor()
        cur.executescript(
            """
            PRAGMA foreign_keys = ON;
            
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            );
    
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT
            );
            """
        )
        self.conn.commit()

    def migrate(self) -> None:
        """Idempotent schema ensure—creates any tables we might have added later."""
        self._init_db()  # runs the same CREATE IF NOT EXISTS script again
    # ---------------Users ---------------------
    def get_or_create_user(self, username: str = "default") -> User:
        """Return existing user or create it"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row:
            return User(id=row["id"], username=row["username"])
        cur.execute("INSERT INTO users(username) VALUES (?)", (username,))
        self.conn.commit()
        return User(id=cur.lastrowid, username = username)

    #--------------Categories ------------------
    def add_category(self,name: str, color: Optional[str] = None) -> Category:
        """Create a category and return it (generated id)"""
        cur = self.conn.cursor()
        cur.execute("INSERT INTO categories (name, color) VALUES (?, ?)", (name, color))
        self.conn.commit()
        return Category(id = cur.lastrowid, name = name, color = color)

    def list_categories(self) -> List[Category]:
        """Return all categories sorted by name (for sidebar)"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM categories ORDER BY name ASC")
        return [Category(id = r["id"], name = r["name"], color = r["color"]) for r in cur.fetchall()]
