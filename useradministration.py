import sqlite3
from pathlib import Path
import hashlib
from typing import Optional


class UserAdministration:
    def __init__(self, db_path: str = "user.db") -> None:
        self.db_path = db_path
        self._ensure_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _ensure_db(self) -> None:
        Path(self.db_path).touch(exist_ok=True)
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS benutzer (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    passwort_hash TEXT NOT NULL,
                    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    @staticmethod
    def _hash_passwort(passwort: str) -> str:
        return hashlib.sha256(passwort.encode("utf-8")).hexdigest()

    def username_exisist(self, username: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM benutzer WHERE username = ?", (username,))
            return cur.fetchone() is not None

    def email_exists(self, email: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM benutzer WHERE email = ?", (email,))
            return cur.fetchone() is not None

    def add_user(self, username: str, email: str, passwort: str) -> bool:
        passwort_hash = self._hash_passwort(passwort)

        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO benutzer (username, email, passwort_hash)
                    VALUES (?, ?, ?)
                    """,
                    (username, email, passwort_hash),
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Verletzung UNIQUE-Constraint (username oder email existiert)
            return False

    def verify_login(self, username: str, passwort: str) -> bool:
        passwort_hash = self._hash_passwort(passwort)
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM benutzer
                WHERE username = ? AND passwort_hash = ?
                """,
                (username, passwort_hash),
            )
            result = cur.fetchone()
            return result is not None

    def get_user_by_name(self, username: str) -> Optional[dict]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, username, email, erstellt_am
                FROM benutzer
                WHERE username = ?
                """,
                (username,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "erstellt_am": row[3],
            }

