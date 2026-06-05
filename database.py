import aiosqlite
from typing import Any
from datetime import datetime
from logger_config import logger

DB_PATH = 'tutor_bot.db'


class Database:

    def __init__(self, db_path: str = DB_PATH):
        self._path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def initialize(self):
        self._conn = await aiosqlite.connect(self._path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute('PRAGMA foreign_keys = ON')
        await self._db_init()
        logger.info('Database initialized')

    async def _db_init(self):
        tables = [
            'CREATE TABLE IF NOT EXISTS admins (admin_id INTEGER)',
            '''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                role TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )''',
            '''CREATE TABLE IF NOT EXISTS tutors (
                user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                name TEXT, age INTEGER, photo_file_id TEXT, subject TEXT,
                experience INTEGER, info TEXT, contacts TEXT, price REAL
            )''',
            '''CREATE TABLE IF NOT EXISTS tutees (
                user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                name TEXT, age INTEGER, subject TEXT, place TEXT,
                target TEXT, contacts TEXT, price REAL
            )''',
            '''CREATE TABLE IF NOT EXISTS requests (
                user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
                created_at TEXT DEFAULT (datetime('now')),
                status TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS scheduled_posts (
                post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_date TEXT,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                status TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tutor_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                reviewer_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(tutor_id, reviewer_id)
            )''',
            '''CREATE TABLE IF NOT EXISTS profile_views (
                tutor_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                viewed_at TEXT DEFAULT (datetime('now'))
            )''',
        ]
        for sql in tables:
            await self._conn.execute(sql)
        await self._conn.commit()

        migrations = [
            "ALTER TABLE tutors ADD COLUMN photo_file_id TEXT",
            "ALTER TABLE users ADD COLUMN created_at TEXT DEFAULT (datetime('now'))",
        ]
        for sql in migrations:
            try:
                await self._conn.execute(sql)
                await self._conn.commit()
            except Exception:
                pass

    def _ph(self, lst):
        return ','.join(['?' for _ in lst])

    # --- Scheduled posts ---

    async def add_scheduled_post(self, user_id: int, date: datetime, status: str):
        await self._conn.execute(
            'INSERT INTO scheduled_posts(user_id, post_date, status) VALUES(?, ?, ?)',
            (user_id, date.isoformat(), status)
        )
        await self._conn.commit()

    async def get_ready_scheduled_posts(self):
        cur = await self._conn.execute(
            "SELECT post_id, user_id, post_date, status FROM scheduled_posts "
            "WHERE status = 'pending' AND post_date <= datetime('now')"
        )
        return [dict(row) for row in await cur.fetchall()]

    async def update_scheduled_post(self, post_id: int, status: str):
        await self._conn.execute('UPDATE scheduled_posts SET status = ? WHERE post_id = ?', (status, post_id))
        await self._conn.commit()

    async def get_user_scheduled_posts(self, user_id: int):
        cur = await self._conn.execute(
            'SELECT post_id, user_id, post_date, status FROM scheduled_posts WHERE user_id = ?', (user_id,)
        )
        return [dict(row) for row in await cur.fetchall()]

    # --- Requests ---

    async def upsert_request(self, user_id: int, created_at: datetime = None, status: str = 'pending'):
        if created_at is None:
            created_at = datetime.now()
        await self._conn.execute(
            'INSERT INTO requests(user_id, created_at, status) VALUES(?, ?, ?) '
            'ON CONFLICT(user_id) DO UPDATE SET status = excluded.status, created_at = excluded.created_at',
            (user_id, created_at.isoformat(), status)
        )
        await self._conn.commit()

    async def get_request(self, user_id: int, status: str = 'pending'):
        cur = await self._conn.execute(
            'SELECT user_id, status FROM requests WHERE user_id = ? AND status = ?', (user_id, status)
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def get_requests_by_status(self, statuses: list[str] = None):
        statuses = statuses or ['pending', 'finished']
        cur = await self._conn.execute(
            f'SELECT user_id, status, created_at FROM requests WHERE status IN ({self._ph(statuses)})',
            statuses
        )
        return [dict(row) for row in await cur.fetchall()]

    # --- Users ---

    async def create_user(self, user_id: int, role: str, name: str = None, age: int = None,
                          photo_file_id: str = None, subject: str = None, experience: int = None,
                          info: str = None, contacts: str = None, price: float = None,
                          place: str = None, target: str = None):
        await self._conn.execute('INSERT OR IGNORE INTO users(user_id, role) VALUES(?, ?)', (user_id, role))
        if role == 'tutor':
            await self._conn.execute(
                'INSERT OR IGNORE INTO tutors(user_id, name, age, photo_file_id, subject, experience, info, contacts, price) '
                'VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (user_id, name, age, photo_file_id, subject, experience, info, contacts, price)
            )
        else:
            await self._conn.execute(
                'INSERT OR IGNORE INTO tutees(user_id, name, age, subject, place, target, contacts, price) '
                'VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
                (user_id, name, age, subject, place, target, contacts, price)
            )
        await self._conn.commit()

    async def get_user(self, user_id: int):
        cur = await self._conn.execute('SELECT user_id, role FROM users WHERE user_id = ?', (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None

    async def get_users_by_role(self, role: str = None) -> list[dict]:
        if role:
            cur = await self._conn.execute('SELECT user_id FROM users WHERE role = ?', (role,))
        else:
            cur = await self._conn.execute('SELECT user_id FROM users')
        return [dict(row) for row in await cur.fetchall()]

    _ALLOWED_FIELDS = {'name', 'age', 'photo_file_id', 'subject', 'experience', 'info', 'contacts', 'price', 'place', 'target'}

    async def update_user(self, user_id: int, field: str, value: Any, role: str):
        if field not in self._ALLOWED_FIELDS:
            raise ValueError(f'Invalid field: {field}')
        table = 'tutors' if role == 'tutor' else 'tutees'
        await self._conn.execute(f'UPDATE {table} SET {field} = ? WHERE user_id = ?', (value, user_id))
        await self._conn.commit()

    async def get_admins(self):
        cur = await self._conn.execute('SELECT admin_id FROM admins')
        return [row['admin_id'] for row in await cur.fetchall()]

    async def add_admin(self, admin_id: int):
        await self._conn.execute('INSERT INTO admins(admin_id) VALUES(?)', (admin_id,))
        await self._conn.commit()

    async def get_tutor_data(self, user_id: int):
        cur = await self._conn.execute(
            'SELECT user_id, name, age, photo_file_id, subject, experience, info, contacts, price '
            'FROM tutors WHERE user_id = ?', (user_id,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    async def get_tutee_data(self, user_id: int):
        cur = await self._conn.execute(
            'SELECT user_id, name, age, subject, place, target, contacts, price '
            'FROM tutees WHERE user_id = ?', (user_id,)
        )
        row = await cur.fetchone()
        return dict(row) if row else None

    # --- Reviews ---

    async def add_review(self, tutor_id: int, reviewer_id: int, rating: int, comment: str = None):
        await self._conn.execute(
            'INSERT OR REPLACE INTO reviews(tutor_id, reviewer_id, rating, comment) VALUES(?, ?, ?, ?)',
            (tutor_id, reviewer_id, rating, comment)
        )
        await self._conn.commit()

    async def get_tutor_reviews(self, tutor_id: int, limit: int = 5):
        cur = await self._conn.execute(
            'SELECT rating, comment, created_at FROM reviews WHERE tutor_id = ? ORDER BY created_at DESC LIMIT ?',
            (tutor_id, limit)
        )
        return [dict(row) for row in await cur.fetchall()]

    async def get_tutor_rating(self, tutor_id: int) -> tuple[float, int]:
        cur = await self._conn.execute(
            'SELECT AVG(rating) as avg_r, COUNT(*) as cnt FROM reviews WHERE tutor_id = ?', (tutor_id,)
        )
        row = await cur.fetchone()
        return (round(row['avg_r'], 1) if row['avg_r'] else 0.0, row['cnt'])

    async def has_reviewed(self, tutor_id: int, reviewer_id: int) -> bool:
        cur = await self._conn.execute(
            'SELECT 1 FROM reviews WHERE tutor_id = ? AND reviewer_id = ?', (tutor_id, reviewer_id)
        )
        return await cur.fetchone() is not None

    # --- Profile views ---

    async def add_profile_view(self, tutor_id: int):
        await self._conn.execute('INSERT INTO profile_views(tutor_id) VALUES(?)', (tutor_id,))
        await self._conn.commit()

    async def get_views_last_7_days(self, tutor_id: int) -> int:
        cur = await self._conn.execute(
            "SELECT COUNT(*) as cnt FROM profile_views WHERE tutor_id = ? AND viewed_at >= datetime('now', '-7 days')",
            (tutor_id,)
        )
        row = await cur.fetchone()
        return row['cnt']

    async def get_tutors_with_views(self):
        cur = await self._conn.execute(
            "SELECT DISTINCT tutor_id FROM profile_views WHERE viewed_at >= datetime('now', '-7 days')"
        )
        return [row['tutor_id'] for row in await cur.fetchall()]

    # --- Dashboard ---

    async def get_dashboard_stats(self) -> dict:
        stats = {}
        queries = {
            'tutors': "SELECT COUNT(*) FROM users WHERE role='tutor'",
            'tutees': "SELECT COUNT(*) FROM users WHERE role='tutee'",
            'pending': "SELECT COUNT(*) FROM requests WHERE status='pending'",
            'published_7d': "SELECT COUNT(*) FROM requests WHERE status='finished' AND created_at >= datetime('now','-7 days')",
            'scheduled': "SELECT COUNT(*) FROM scheduled_posts WHERE status='pending'",
            'avg_rating': "SELECT ROUND(AVG(rating),1) FROM reviews",
        }
        for key, sql in queries.items():
            cur = await self._conn.execute(sql)
            row = await cur.fetchone()
            stats[key] = row[0] or 0
        return stats

    async def get_recent_users(self, limit: int = 20):
        cur = await self._conn.execute(
            '''SELECT u.user_id, u.role, u.created_at,
               COALESCE(t.name, tt.name) as name,
               COALESCE(t.subject, tt.subject) as subject
               FROM users u
               LEFT JOIN tutors t ON u.user_id = t.user_id AND u.role='tutor'
               LEFT JOIN tutees tt ON u.user_id = tt.user_id AND u.role='tutee'
               ORDER BY u.created_at DESC LIMIT ?''',
            (limit,)
        )
        return [dict(row) for row in await cur.fetchall()]
