"""
Programmname: Authentication

Autor: Maximilian Pfau

Datum: 13.01.2026

Beschreibung:
Verwaltet Benutzer-Sitzungen und Validierung. Nutzt zentrale Methoden zur
Prüfung von E-Mail-Syntax und Passwortstärke.


Quellen:
- Programmierung
    - Lehrbrief zur Vorlesung
    - https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
    - ChatGPT 5.2
"""

import streamlit as st
import os
import json
import re
import logging
from email.utils import parseaddr
from databaseHandler import DatabaseAdministration
import appconfig


class Authentication:
    """
    Klasse zur Handhabung von Benutzer-Sitzungen und Validierung von Nutzerdaten.
    """

    def __init__(self):
        self.user_administration = DatabaseAdministration()
        self._EMAIL_REGEX = re.compile(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        )
        self.KEY_LOGGED_IN = appconfig.KEY_LOGGED_IN
        self.KEY_USERNAME = appconfig.KEY_USERNAME
        self.KEY_USER = appconfig.KEY_USER
        self.KEY_AUTH_ERROR = appconfig.KEY_AUTH_ERROR
        self.KEY_AUTH_INFO = appconfig.KEY_AUTH_INFO
        self.AUTH_FILE = appconfig.AUTH_FILE
        # Defaults nur setzen, wenn Key noch nicht existiert (nicht überschreiben)
        st.session_state.setdefault(self.KEY_LOGGED_IN, False)
        st.session_state.setdefault(self.KEY_USERNAME, "Gast")
        st.session_state.setdefault(self.KEY_USER, None)
        st.session_state.setdefault(self.KEY_AUTH_ERROR, None)
        st.session_state.setdefault(self.KEY_AUTH_INFO, None)

    # persistente Fehlermeldung über st.rerun() hinweg
    # Instanzmethode
    def _set_error(self, msg: str | None) -> None:
        st.session_state[self.KEY_AUTH_ERROR] = msg

    def _set_info(self, msg: str | None) -> None:
        st.session_state[self.KEY_AUTH_INFO] = msg

    def clear_messages(self) -> None:
        self._set_error(None)
        self._set_info(None)

    def _is_valid_email(self, email: str) -> bool:
        if not email:
            return False
        _, addr = parseaddr(email)
        if not addr or addr != email:
            return False
        return bool(self._EMAIL_REGEX.match(email))

    def validate_email_syntax(self, email: str) -> bool:
        """Zentrale Prüfung der E-Mail-Syntax."""
        """
        E-Mail-Syntaxprüfung

        1) parseaddr:
           - prüft RFC-Struktur
           - filtert Müll wie 'foo@@bar'
           - extrahiert echte Adresse aus 'Name <mail@domain>'

        2) Regex:
           - erzwingt Praxis-Regeln
           - verhindert 'foo@bar', 'a@b', 'foo@localhost'
        """
        if not self._is_valid_email(email.strip().lower()):
            return False
        return True

    def validate_password_strength(self, password: str) -> bool:
        """Zentrale Prüfung der Passwort-Mindestanforderungen."""
        if not password or len(password) < 6:
            return False
        return True

    def consume_messages(self) -> tuple[str | None, str | None]:
        # Gibt err, info zurück und löscht sie danach aus dem Session-State
        err = st.session_state.get(self.KEY_AUTH_ERROR)
        info = st.session_state.get(self.KEY_AUTH_INFO)
        st.session_state[self.KEY_AUTH_ERROR] = None
        st.session_state[self.KEY_AUTH_INFO] = None
        return err, info

    def login(self, username: str, password: str):
        self.clear_messages()
        if not username or not password:
            self._set_error("Bitte Benutzername und Passwort ausfüllen!")
            return None

        if self.user_administration.verify_login(username, password):
            user = self.user_administration.get_user_by_name(username)
            st.session_state[self.KEY_LOGGED_IN] = True
            st.session_state[self.KEY_USERNAME] = username
            st.session_state[self.KEY_USER] = user

            try:
                with open(self.AUTH_FILE, "w") as f:
                    json.dump(user, f)
            except Exception:
                logging.exception("Fehler beim Schreiben der AUTH_FILE")
            self._set_info("Erfolgreich eingeloggt!")
            return user

        self._set_error("Ungültige Anmeldedaten!")
        return None

    def logout(self) -> None:
        self.clear_messages()
        st.session_state[self.KEY_LOGGED_IN] = False
        st.session_state[self.KEY_USERNAME] = "Gast"
        st.session_state[self.KEY_USER] = None
        st.session_state["auth_tab"] = "Login"

        try:
            if os.path.exists(self.AUTH_FILE):
                os.remove(self.AUTH_FILE)
        except Exception:
            logging.exception("Fehler beim Löschen der AUTH_FILE")

        self._set_info("Erfolgreich ausgeloggt.")

    def register(
        self, username: str, email: str, password: str, gemini_key: str
    ) -> bool:
        self.clear_messages()

        if not username or not email or not password or not gemini_key:
            self._set_error("Bitte alle Felder ausfüllen!")
            return False

        if not self.validate_password_strength(password):
            self._set_error("Das Passwort muss mindestens 6 Zeichen lang sein!")
            return False

        if not self.validate_email_syntax(email):
            self._set_error("Bitte eine gültige E-Mail-Adresse eingeben!")
            return False

        if self.user_administration.username_exists(username):
            self._set_error("Benutzername bereits vergeben!")
            return False

        # Normalisierung:
        # - strip(): entfernt führende/trailing Spaces (Copy/Paste-Fehler)
        # - lower(): Domain ist case-insensitive, Praxis-Standard
        if self.user_administration.email_exists(email.strip().lower()):
            self._set_error("E-Mail bereits registriert!")
            return False

        if self.user_administration.add_user(
            username, email.strip().lower(), password, gemini_key
        ):
            self._set_info("Konto erfolgreich angelegt!")
            return True

        return False

    def restore_session(self) -> None:
        if st.session_state[self.KEY_LOGGED_IN]:
            return

        if not os.path.exists(self.AUTH_FILE):
            return  # völlig normal, nichts zu restaurieren

        try:
            with open(self.AUTH_FILE, "r") as f:
                user = json.load(f)

            if not user:
                return

            st.session_state[self.KEY_LOGGED_IN] = True
            st.session_state[self.KEY_USER] = user
            st.session_state[self.KEY_USERNAME] = user.get("username", "Gast")

        except json.JSONDecodeError:
            logging.error("AUTH_FILE ist beschädigt (JSON ungültig)")
        except Exception:
            logging.exception("Unerwarteter Fehler beim Session-Restore")
