import sqlite3
from typing import List, Optional

from models import User, Category, Task, to_iso_date, from_iso_date, now_iso_ts

DB_PATH = "planpal.sqlite3"


class Storage:
    """Small wrapper around sqlite for now"""

    def __init__(self, path: str = DB_PATH):
        # Connect and enable dict-like row access
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """Create/ensure schema """
        cur = self.conn.cursor()
        cur.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                color TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) on DELETE CASCADE
            );

            
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                due_date TEXT,  -- YYYY-MM-DD
                priority TEXT CHECK (priority IN ('Low','Medium','High')) NOT NULL DEFAULT 'Medium',
                status   TEXT CHECK (status   IN ('Todo','Done'))         NOT NULL DEFAULT 'Todo',
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                completed_at TEXT,
                FOREIGN KEY (user_id)     REFERENCES users(id)      ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
            );
            """
        )
        self.conn.commit()

    def migrate(self) -> None:
        """Idempotent schema ensure—creates any tables we might have added later."""
        self._init_db()  # runs the same CREATE IF NOT EXISTS script again

    # ---------------Users ---------------------

    def create_user(self, username: str, password: str) -> User:
        """Create a new user; raises sqlite3.IntegrityError if username exists."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO users(username, password) VALUES (?, ?)",
            (username, password),
        )
        self.conn.commit()
        return User(id=cur.lastrowid, username=username, password=password)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Return User if username/password match, else None."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        row = cur.fetchone()
        if not row:
            return None
        return User(
            id=row["id"],
            username=row["username"],
            password=row["password"],
        )

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Fetch a user by username, or None if not found."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            return None
        return User(
            id=row["id"],
            username=row["username"],
            password=row["password"],
        )

    def get_or_create_user(self, username: str = "default") -> User:
        """
        Backward-compatible helper used by older code paths.
        Fetch user if it exists, otherwise create one with a default password.
        """
        user = self.get_user_by_username(username)
        if user:
            return user
        # Default password only used for this helper.
        return self.create_user(username, "password")

    #--------------Categories ------------------

    def add_category(self, user_id: int, name: str, color: Optional[str] = None) -> Category:
        """Create a category for a specific user and return it."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO categories (user_id, name, color) VALUES (?, ?, ?)",
            (user_id, name, color),
        )
        self.conn.commit()
        return Category(id=cur.lastrowid, user_id=user_id, name=name, color=color)

    def list_categories(self, user_id: int) -> List[Category]:
        """Return all categories for a user, sorted by name (for sidebar)."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM categories WHERE user_id = ? ORDER BY name ASC",
            (user_id,),
        )
        return [
            Category(
                id=r["id"],
                user_id=r["user_id"],
                name=r["name"],
                color=r["color"],
            )
            for r in cur.fetchall()
        ]

    def delete_category(self, category_id: int) -> None:
        """Delete a category by id."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        self.conn.commit()

    #------------ TASKS ------------

    def add_task(
        self,
        user_id: int,
        title: str,
        description: str = "",
        category_id: Optional[int] = None,
        due_date: Optional["date"] = None,
        priority: str = "Medium",
    ) -> Task:
        """Insert a new task into DB and return it."""
        now = now_iso_ts()
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO tasks
               (user_id, category_id, title, description, due_date,
                priority, status, created_at, updated_at)
               VALUES (?,?,?,?,?,?, 'Todo', ?, ?)""",
            (
                user_id,
                category_id,
                title,
                description,
                to_iso_date(due_date),
                priority,
                now,
                now,
            ),
        )
        self.conn.commit()
        return self.get_task(cur.lastrowid)

    def update_task(
        self,
        task_id: int,
        title: str,
        description: str,
        category_id: Optional[int],
        due_date,
        priority: str,
    ) -> Task:
        """Update an existing task."""
        now = now_iso_ts()
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, category_id = ?, due_date = ?,
                priority = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, description, category_id, to_iso_date(due_date), priority, now, task_id),
        )
        self.conn.commit()
        return self.get_task(task_id)

    def delete_task(self, task_id: int) -> None:
        """Delete task by ID."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def get_task(self, task_id: int) -> Task:
        """Fetch a single task by id."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        r = cur.fetchone()
        return Task(
            id=r["id"],
            user_id=r["user_id"],
            category_id=r["category_id"],
            title=r["title"],
            description=r["description"] or "",
            due_date=from_iso_date(r["due_date"]),
            priority=r["priority"],
            status=r["status"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            completed_at=r["completed_at"],
        )

    def list_tasks(self, user_id: int) -> List[Task]:
        """List all tasks for a user (ordered by due date and priority)."""
        cur = self.conn.cursor()
        cur.execute(
            """
        SELECT * FROM tasks
        WHERE user_id = ?
        ORDER BY (due_date IS NULL), due_date ASC,
                 CASE priority
                     WHEN 'High' THEN 3
                     WHEN 'Medium' THEN 2
                     ELSE 1
                 END DESC
        """,
            (user_id,),
        )
        rows = cur.fetchall()
        return [
            Task(
                id=r["id"],
                user_id=r["user_id"],
                category_id=r["category_id"],
                title=r["title"],
                description=r["description"] or "",
                due_date=from_iso_date(r["due_date"]),
                priority=r["priority"],
                status=r["status"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                completed_at=r["completed_at"],
            )
            for r in rows
        ]
