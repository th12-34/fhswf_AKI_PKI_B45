import sqlite3
from pathlib import Path
import hashlib
from typing import Optional, List, Dict, Any


class DatabaseAdministration:
    def __init__(self, db_path: str = "user.db") -> None:
        self.db_path = db_path
        self._ensure_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        # important for ON DELETE/UPDATE CASCADE
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _ensure_db(self) -> None:
        Path(self.db_path).touch(exist_ok=True)
        with self._get_connection() as conn:
            cur = conn.cursor()

            # users table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    passwort_hash TEXT NOT NULL,
                    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            # portfolio table (one user → many portfolios)
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

            # assets table (one portfolio → many assets)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER NOT NULL,
                    asset_type TEXT NOT NULL,      -- 'crypto' or 'stock'
                    asset_symbol TEXT NOT NULL,    -- e.g. 'BTC', 'AAPL'
                    asset_name TEXT,
                    amount REAL NOT NULL,
                    buy_price REAL NOT NULL,       -- per unit
                    bought_at TIMESTAMP NOT NULL,  -- when it was bought
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
    def _hash_passwort(passwort: str) -> str:
        return hashlib.sha256(passwort.encode("utf-8")).hexdigest()

    # --------- User functions ---------

    def username_exisist(self, username: str) -> bool: 
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            return cur.fetchone() is not None

    def email_exists(self, email: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM users WHERE email = ?", (email,))
            return cur.fetchone() is not None

    def add_user(self, username: str, email: str, passwort: str) -> bool:
        """
        Creates a user and automatically creates a default portfolio for them.
        """
        passwort_hash = self._hash_passwort(passwort)

        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO users (username, email, passwort_hash)
                    VALUES (?, ?, ?)
                    """,
                    (username, email, passwort_hash),
                )

                cur.execute(
                    """
                    INSERT INTO portfolio (portfolio_username, portfolio_name)
                    VALUES (?, ?)
                    """,
                    (username, "Standard-Portfolio"),
                )

                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_login(self, username: str, passwort: str) -> bool:
        passwort_hash = self._hash_passwort(passwort)
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM users
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
                FROM users
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

    # --------- Portfolio functions ---------

    def create_portfolio(self, username: str, portfolio_name: str) -> Optional[int]:
        """
        Creates an additional portfolio for an existing user.
        Returns the new portfolio id or None on error.
        """
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO portfolio (portfolio_username, portfolio_name)
                    VALUES (?, ?)
                    """,
                    (username, portfolio_name),
                )
                portfolio_id = cur.lastrowid
                conn.commit()
                return portfolio_id
        except sqlite3.IntegrityError:
            return None
        
    def delete_portfolio(self, username: str, portfolio_id: int) -> bool:
        """
        Deletes a portfolio by its ID for a specific user.
        Returns True if successful, False if something went wrong.
        """
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
               
                cur.execute(
                    """
                    DELETE FROM portfolio 
                    WHERE id = ? AND portfolio_username = ?
                    """,
                    (portfolio_id, username),
                )
                conn.commit()
                
                # Check if a row was actually deleted
                if cur.rowcount > 0:
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def get_portfolios_for_user(self, username: str):
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, portfolio_name 
                FROM portfolio 
                WHERE portfolio_username = ? 
                ORDER BY id
                """, 
                (username,)
            )
            rows = cur.fetchall()
            
            portfolio_list = []
    
            for row in rows:
                portfolio_id = row[0]
                name = row[1]
                portfolio_list.append( (portfolio_id, name) )
                
            return portfolio_list
        
    def get_portfolio_ids(self, username: str):
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM portfolio WHERE portfolio_username = ?", (username,))
            
            rows = cur.fetchall()
            
            id_list = []
            
            for row in rows:
                portfolio_id = row[0]
                id_list.append(portfolio_id)
                
            return id_list

    # --------- Asset functions ---------

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
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO assets
                    (portfolio_id, asset_type, asset_symbol, asset_name, amount, buy_price, bought_at, currency)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        portfolio_id,
                        asset_type,
                        asset_symbol,
                        asset_name,
                        amount,
                        buy_price,   # schon EUR
                        bought_at,
                        "EUR",       # immer EUR speichern
                    ),
                )
                asset_id = cur.lastrowid
                conn.commit()
                return asset_id
        except sqlite3.IntegrityError:
            return None
        

    def get_assets_for_portfolio(self, portfolio_id: int) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, asset_type, asset_symbol, asset_name, amount, buy_price, bought_at
                FROM assets
                WHERE portfolio_id = ?
                ORDER BY bought_at
                """,
                (portfolio_id,),
            )
            rows = cur.fetchall()

            all_assets = []

            for r in rows:
                asset_dict = {}

                asset_dict["portfolio_id"] = r[0]
                asset_dict["asset_type"] = r[1]
                asset_dict["asset_symbol"] = r[2]
                asset_dict["asset_name"] = r[3]
                asset_dict["amount"] = r[4]
                asset_dict["buy_price"] = r[5]
                asset_dict["bought_at"] = r[6]


                all_assets.append(asset_dict)

            return all_assets


    def delete_asset(self, asset_id: int) -> bool:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
            conn.commit()
            return cur.rowcount > 0

