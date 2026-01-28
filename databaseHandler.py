"""
Klasse: DatabaseAdministration

Autor: Bastian Pivarcsi

Datum: 13.01.2026

Beschreibung:
Diese Klasse übernimmt die Verwaltung einer SQLite-Datenbank für ein Portfolio-Management-System.
Sie bietet Funktionen zur Nutzerregistrierung, Authentifizierung sowie zur Verwaltung
von Portfolios, Assets und der Speicherung von Gemini API Keys.


Quellen:
- Programmierung
    - Lehrbrief zur Vorlesung
    - Gemini
    - https://docs.python.org/3/library/sqlite3.html
    - https://docs.python.org/3/library/hashlib.html
"""

import sqlite3
import logging
import hashlib
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from appconfig import DATABASE_NAME

# Grundkonfiguration für das Logging
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)


class DatabaseAdministration:
    """
    Diese Klasse stellt Methoden bereit, um Nutzerdaten, Portfolios und Assets
    in einer lokalen SQLite-Datenbank zu verwalten.
    """

    def __init__(self, db_path: str = DATABASE_NAME) -> None:
        """
        Initialisiert die Datenbankverbindung und stellt sicher, dass alle Tabellen existieren.

        :param db_path: Pfad zur SQLite-Datenbankdatei
        :return: -
        """
        self.db_path = db_path
        self._ensure_db()

    def _get_connection(self):
        """
        Erstellt eine Verbindung zur SQLite-Datenbank und aktiviert Fremdschlüssel-Constraints.

        :return: sqlite3.Connection Objekt
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _ensure_db(self) -> None:
        """
        Erzeugt die Datenbankdatei und die notwendigen Tabellen, falls diese noch nicht existieren.

        :return: -
        """
        Path(self.db_path).touch(exist_ok=True)
        with self._get_connection() as conn:
            cur = conn.cursor()

            # Nutzertabelle
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    passwort_hash TEXT NOT NULL,
                    gemini_api_key TEXT,
                    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # Portfolio-Tabelle
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolio (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_username TEXT NOT NULL,
                    portfolio_name TEXT NOT NULL,
                    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (portfolio_username)
                        REFERENCES users(username)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                );
                """
            )

            # Asset-Tabelle
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER NOT NULL,
                    asset_type TEXT NOT NULL,
                    asset_symbol TEXT NOT NULL,
                    asset_name TEXT,
                    amount REAL NOT NULL,
                    buy_price REAL NOT NULL,
                    bought_at TIMESTAMP NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'EUR',
                    FOREIGN KEY (portfolio_id)
                        REFERENCES portfolio(id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                );
                """
            )
            conn.commit()

    @staticmethod
    def hash_password(passwort: str) -> str:
        """
        Hasht ein Passwort mittels SHA-256 zur sicheren Speicherung.

        :param passwort: Das Passwort im Klartext
        :return: Gehashtes Passwort als String
        """
        return hashlib.sha256(passwort.encode("utf-8")).hexdigest()

    # --------- Nutzer-Funktionen ---------

    def username_exists(self, username: str) -> bool:
        """
        Prüft, ob ein Benutzername bereits in der Datenbank vergeben ist.

        :param username: Der zu prüfende Name
        :return: True wenn vorhanden, sonst False
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            return cur.fetchone() is not None

    def email_exists(self, email: str) -> bool:
        """
        Prüft, ob eine E-Mail-Adresse bereits registriert ist.

        :param email: Die zu prüfende E-Mail
        :return: True wenn vorhanden, sonst False
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM users WHERE email = ?", (email,))
            return cur.fetchone() is not None

    def add_user(
        self, username: str, email: str, passwort: str, gemini_key: str
    ) -> bool:
        """
        Legt einen neuen Nutzer an und erstellt automatisch ein Standard-Portfolio.

        :param username: Gewünschter Benutzername
        :param email: E-Mail des Nutzers
        :param passwort: Passwort im Klartext
        :param gemini_key: Gemini API Key im Klartext
        :return: True bei Erfolg, False bei Fehlern
        """
        passwort_hash = self.hash_password(passwort)

        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users (username, email, passwort_hash, gemini_api_key) VALUES (?, ?, ?, ?)",
                    (username, email, passwort_hash, gemini_key),
                )
                cur.execute(
                    "INSERT INTO portfolio (portfolio_username, portfolio_name) VALUES (?, ?)",
                    (username, "Standard-Portfolio"),
                )
                conn.commit()
            return True
        except json.JSONDecodeError:
            logging.error("AUTH_FILE ist beschädigt (JSON ungültig)")
            return False
        except Exception:
            logging.exception("Unerwarteter Fehler beim Session-Restore")
            return False

    def verify_login(self, username: str, passwort: str) -> bool:
        """
        Validiert die Anmeldedaten eines Nutzers.

        :param username: Benutzername
        :param passwort: Passwort im Klartext
        :return: True wenn Login korrekt, sonst False
        """
        passwort_hash = self.hash_password(passwort)
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM users WHERE username = ? AND passwort_hash = ?",
                (username, passwort_hash),
            )
            return cur.fetchone() is not None

    def get_user_by_name(self, username: str) -> Optional[dict]:
        """
        Ruft die Profildaten eines Nutzers ab.

        :param username: Benutzername
        :return: Dictionary mit Nutzerdaten oder None
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, email, erstellt_am FROM users WHERE username = ?",
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

    def get_gemini_api_key(self, username: str) -> Optional[str]:
        """
        Liest den gespeicherten Gemini API Key eines Nutzers aus.

        :param username: Benutzername
        :return: Der API Key als String oder None
        """
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT gemini_api_key FROM users WHERE username = ?", (username,)
                )
                row = cur.fetchone()
                return row[0] if row else None
        except Exception:
            logging.exception("Unerwarteter Fehler beim Lesen des API Keys")
            return None

    def update_user_settings(
        self, username, new_email, new_password_hash=None, new_gemini_key=None
    ):
        """Aktualisiert die Profildaten eines Nutzers in der Datenbank."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                # E-Mail und Gemini Key immer aktualisieren
                cur.execute(
                    "UPDATE users SET email = ?, gemini_api_key = ? WHERE username = ?",
                    (new_email, new_gemini_key, username),
                )
                # Passwort nur aktualisieren, wenn ein neues gesetzt wurde
                if new_password_hash:
                    cur.execute(
                        "UPDATE users SET passwort_hash = ? WHERE username = ?",
                        (new_password_hash, username),
                    )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Fehler beim Profil-Update: {e}")
            return False

    def delete_user_account(self, username):
        """Löscht einen Nutzer und alle zugehörigen Daten aus der Datenbank."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                # Falls Fremdschlüssel aktiviert sind, löscht dies auch Portfolios/Assets
                cur.execute("DELETE FROM users WHERE username = ?", (username,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Fehler beim Löschen des Kontos: {e}")
            return False

    # --------- Portfolio-Funktionen ---------

    def create_portfolio(self, username: str, portfolio_name: str) -> Optional[int]:
        """
        Erstellt ein weiteres Portfolio für einen Nutzer.

        :param username: Benutzername
        :param portfolio_name: Name des neuen Portfolios
        :return: ID des neuen Portfolios oder None
        """
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO portfolio (portfolio_username, portfolio_name) VALUES (?, ?)",
                    (username, portfolio_name),
                )
                p_id = cur.lastrowid
                conn.commit()
                return p_id
        except Exception:
            logging.exception("Unerwarteter Fehler beim Erstellen des Portfolios")
            return None

    def delete_portfolio(self, username: str, portfolio_id: int) -> bool:
        """
        Löscht ein Portfolio des Nutzers.

        :param username: Besitzer des Portfolios
        :param portfolio_id: ID des zu löschenden Portfolios
        :return: True bei Erfolg, sonst False
        """
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "DELETE FROM portfolio WHERE id = ? AND portfolio_username = ?",
                    (portfolio_id, username),
                )
                conn.commit()
                return cur.rowcount > 0
        except Exception:
            logging.exception("Unerwarteter Fehler beim Löschen des Portfolios")
            return False

    def get_portfolio_ids(self, username: str) -> List[int]:
        """
        Gibt eine Liste aller Portfolio-IDs eines Nutzers zurück.

        :param username: Benutzername
        :return: Liste von IDs
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM portfolio WHERE portfolio_username = ?", (username,)
            )
            return [row[0] for row in cur.fetchall()]

    def get_portfolios_for_user(self, username: str) -> List[tuple]:
        """
        Gibt IDs und Namen aller Portfolios eines Nutzers zurück.

        :param username: Benutzername
        :return: Liste von Tupeln (ID, Name)
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, portfolio_name FROM portfolio WHERE portfolio_username = ? ORDER BY id",
                (username,),
            )
            return cur.fetchall()

    # --------- Asset-Funktionen ---------

    def add_asset(
        self,
        portfolio_id: int,
        asset_type: str,
        asset_symbol: str,
        asset_name: Optional[str],
        amount: float,
        buy_price: float,
        bought_at: str,
        currency: str = "EUR",
    ) -> Optional[int]:
        """
        Fügt einem Portfolio ein neues Asset hinzu.

        :param portfolio_id: Ziel-Portfolio ID
        :return: Asset-ID oder None
        """
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO assets (portfolio_id, asset_type, asset_symbol, asset_name, amount, buy_price, bought_at, currency)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        portfolio_id,
                        asset_type,
                        asset_symbol,
                        asset_name,
                        amount,
                        buy_price,
                        bought_at,
                        currency,
                    ),
                )
                a_id = cur.lastrowid
                conn.commit()
                return a_id
        except Exception:
            logging.exception("Unerwarteter Fehler beim Hinzufügen des Assets")
            return None

    def get_assets_for_portfolio(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """
        Ruft alle Assets eines Portfolios ab.

        :param portfolio_id: ID des Portfolios
        :return: Liste von Dictionaries mit Asset-Details
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id, asset_type, asset_symbol, asset_name, amount, buy_price, bought_at, currency FROM assets WHERE portfolio_id = ? ORDER BY bought_at",
                (portfolio_id,),
            )
            rows = cur.fetchall()
            return [
                {
                    "portfolio_id": portfolio_id,
                    "asset_id": r[0],
                    "asset_type": r[1],
                    "asset_symbol": r[2],
                    "asset_name": r[3],
                    "amount": r[4],
                    "buy_price": r[5],
                    "bought_at": r[6],
                    "currency": r[7],
                }
                for r in rows
            ]

    def delete_asset(self, asset_id: int) -> bool:
        """
        Löscht ein Asset aus der Datenbank.

        :param asset_id: ID des Assets
        :return: True bei Erfolg, sonst False
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
            conn.commit()
            return cur.rowcount > 0
