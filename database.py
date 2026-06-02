import sqlite3
from typing import Any
from datetime import datetime

from logger_config import logger

DB_PATH = 'tutor_bot.db'


class Database:

    def __init__(self, db_path: str = DB_PATH) -> None:
        self._path = db_path
        self._session = sqlite3.connect(self._path, check_same_thread=False)
        self._session.row_factory = sqlite3.Row
        self._session.execute('PRAGMA foreign_keys = ON')
        self.db_init()
        logger.info('Database initialized')

    def db_init(self):
        self._session.executescript('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                role TEXT
            );
            CREATE TABLE IF NOT EXISTS tutors (
                user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                name TEXT, age INTEGER, photo_path TEXT, subject TEXT,
                experience INTEGER, info TEXT, contacts TEXT, price REAL
            );
            CREATE TABLE IF NOT EXISTS tutees (
                user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                name TEXT, age INTEGER, subject TEXT, place TEXT,
                target TEXT, contacts TEXT, price REAL
            );
            CREATE TABLE IF NOT EXISTS requests (
                user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                created_at TEXT DEFAULT (datetime('now')),
                status TEXT
            );
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_date TEXT,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                status TEXT
            );
        ''')
        self._session.commit()

    def _ph(self, lst):
        return ','.join(['?' for _ in lst])

    def add_scheduled_post(self, user_id: int, date: datetime, status: str):
        self._session.execute(
            'INSERT INTO scheduled_posts(user_id, post_date, status) VALUES(?, ?, ?)',
            (user_id, date.isoformat(), status)
        )
        self._session.commit()

    def get_scheduled_posts(self, statuses: list[str] = None):
        statuses = statuses or ['pending']
        cur = self._session.execute(
            f'SELECT post_id, user_id, post_date, status FROM scheduled_posts WHERE status IN ({self._ph(statuses)})',
            statuses
        )
        return [dict(row) for row in cur.fetchall()]

    def get_ready_scheduled_posts(self):
        cur = self._session.execute(
            "SELECT post_id, user_id, post_date, status FROM scheduled_posts "
            "WHERE status = 'pending' AND post_date <= datetime('now')"
        )
        return [dict(row) for row in cur.fetchall()]

    def update_scheduled_post(self, post_id: int, status: str):
        self._session.execute('UPDATE scheduled_posts SET status = ? WHERE post_id = ?', (status, post_id))
        self._session.commit()

    def get_user_scheduled_posts(self, user_id: int):
        cur = self._session.execute(
            'SELECT post_id, user_id, post_date, status FROM scheduled_posts WHERE user_id = ?', (user_id,)
        )
        return [dict(row) for row in cur.fetchall()]

    def upsert_request(self, user_id: int, created_at: datetime = None, status: str = 'pending'):
        if created_at is None:
            created_at = datetime.now()
        self._session.execute(
            'INSERT INTO requests(user_id, created_at, status) VALUES(?, ?, ?) '
            'ON CONFLICT(user_id) DO UPDATE SET status = excluded.status, created_at = excluded.created_at',
            (user_id, created_at.isoformat(), status)
        )
        self._session.commit()

    def delete_request(self, user_id: int):
        self._session.execute('DELETE FROM requests WHERE user_id = ?', (user_id,))
        self._session.commit()

    def get_requests(self, limit: int = 10):
        cur = self._session.execute('SELECT user_id, status FROM requests LIMIT ?', (limit,))
        return [dict(row) for row in cur.fetchall()]

    def get_request(self, user_id: int, status: str = 'pending'):
        cur = self._session.execute(
            'SELECT user_id, status FROM requests WHERE user_id = ? AND status = ?', (user_id, status)
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def get_requests_by_status(self, statuses: list[str] = None):
        statuses = statuses or ['pending', 'finished']
        cur = self._session.execute(
            f'SELECT user_id, status, created_at FROM requests WHERE status IN ({self._ph(statuses)})',
            statuses
        )
        return [dict(row) for row in cur.fetchall()]

    def create_user(self, user_id: int, role: str, name: str = None, age: int = None,
                    photo_path: str = None, subject: str = None, experience: int = None,
                    info: str = None, contacts: str = None, price: float = None,
                    place: str = None, target: str = None):
        self._session.execute('INSERT OR IGNORE INTO users(user_id, role) VALUES(?, ?)', (user_id, role))
        if role == 'tutor':
            self._session.execute(
                'INSERT OR IGNORE INTO tutors(user_id, name, age, photo_path, subject, experience, info, contacts, price) '
                'VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (user_id, name, age, photo_path, subject, experience, info, contacts, price)
            )
        else:
            self._session.execute(
                'INSERT OR IGNORE INTO tutees(user_id, name, age, subject, place, target, contacts, price) '
                'VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
                (user_id, name, age, subject, place, target, contacts, price)
            )
        self._session.commit()
        return 1

    def get_user(self, user_id: int):
        cur = self._session.execute('SELECT user_id, role FROM users WHERE user_id = ?', (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_users(self):
        cur = self._session.execute('SELECT user_id, role FROM users')
        return [dict(row) for row in cur.fetchall()]

    def update_user(self, user_id: int, field: str, value: Any, role: str):
        table = 'tutors' if role == 'tutor' else 'tutees'
        self._session.execute(f'UPDATE {table} SET {field} = ? WHERE user_id = ?', (value, user_id))
        self._session.commit()

    def get_admins(self):
        cur = self._session.execute('SELECT admin_id FROM admins')
        return [row['admin_id'] for row in cur.fetchall()]

    def add_admin(self, admin_id: int):
        self._session.execute('INSERT INTO admins(admin_id) VALUES(?)', (admin_id,))
        self._session.commit()

    def get_tutor_data(self, user_id: int):
        cur = self._session.execute(
            'SELECT user_id, name, age, photo_path, subject, experience, info, contacts, price '
            'FROM tutors WHERE user_id = ?', (user_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def get_tutee_data(self, user_id: int):
        cur = self._session.execute(
            'SELECT user_id, name, age, subject, place, target, contacts, price '
            'FROM tutees WHERE user_id = ?', (user_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
