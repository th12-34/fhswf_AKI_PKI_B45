import streamlit as st
import os
import json
import re
import logging
from email.utils import parseaddr
from databaseHandler import DatabaseAdministration

""" AUTH_FILE = "auth.json"

class Authentication:
    def __init__(self):
        self.user_admin = DatabaseAdministration()

    def login(self, username, password):

        if self.user_admin.verify_login(username, password):
            user = self.user_admin.get_user_by_name(username)
            # Save user data to a file
            with open(AUTH_FILE, "w") as f:
                json.dump(user, f)
            return user

        return None

    def get_logged_in_user(self):
        # Check if the auth file exists and return the user data
        if os.path.exists(AUTH_FILE):
            with open(AUTH_FILE, "r") as f:
                return json.load(f)
        return None

    def logout(self):
        # Remove the auth file to log out the user
        if os.path.exists(AUTH_FILE):
            os.remove(AUTH_FILE) """

# Persistente Speicherung der User-Session
AUTH_FILE = "auth.json"

class Authentication:

    # Keys für session_state zentral definieren
    KEY_LOGGED_IN = "logged_in"
    KEY_USERNAME = "username"
    KEY_USER = "user"
    KEY_AUTH_ERROR = "auth_error"
    KEY_AUTH_INFO = "auth_info"

    # Regex für E-Mail Validierung:
    # - genau ein @
    # - Domain mit Punkt
    # - TLD mindestens 2 Zeichen
    _EMAIL_REGEX = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    def __init__(self):
        self.user_administration = DatabaseAdministration()

        # Defaults nur setzen, wenn Key noch nicht existiert (nicht überschreiben)
        st.session_state.setdefault(self.KEY_LOGGED_IN, False)
        st.session_state.setdefault(self.KEY_USERNAME, "Guest")
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
        if not email:
            return False

        _, addr = parseaddr(email)
        if not addr or addr != email:
            return False

        return bool(self._EMAIL_REGEX.match(email))
    
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
                with open(AUTH_FILE, "w") as f:
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
        st.session_state[self.KEY_USERNAME] = "Guest"
        st.session_state[self.KEY_USER] = None
        st.session_state["auth_tab"] = "Login"

        try:
            if os.path.exists(AUTH_FILE):
                os.remove(AUTH_FILE)
        except Exception:
            logging.exception("Fehler beim Löschen der AUTH_FILE beim Logout")
    
        self._set_info("Erfolgreich ausgeloggt.")

    def register (self, username: str, email: str, password: str) -> bool:
        self.clear_messages()

        if not username or not email or not password:
            self._set_error("Bitte alle Felder ausfüllen!")
            return False
        
        if len(password) < 6:
            self._set_error("Das Passwort sollte mindestens 6 Zeichen lang sein!")
            return False
        
        if self.user_administration.username_exisist(username):
            self._set_error("Benutzername ist bereits vergeben!")
            return False
        
        # Normalisierung:
        # - strip(): entfernt führende/trailing Spaces (Copy/Paste-Fehler)
        # - lower(): Domain ist case-insensitive, Praxis-Standard
        email = email.strip().lower()
        
        if not self._is_valid_email(email):
            self._set_error("Bitte eine gültige E-Mail-Adresse eingeben!")
            return False
        
        if self.user_administration.email_exists(email):
            self._set_error("Es existiert bereits ein Konto mit dieser E-Mail!")
            return False

        if self.user_administration.add_user(username, email, password):
            self._set_info("Konto erfolreich angelegt!")
            return True
        
        self._set_error("Beim Anlegen des Kontos ist ein Fehler aufgetreten!")
        return False
    
    def restore_session(self) -> None:
        if st.session_state[self.KEY_LOGGED_IN]:
            return

        if not os.path.exists(AUTH_FILE):
            return  # völlig normal, nichts zu restaurieren

        try:
            with open(AUTH_FILE, "r") as f:
                user = json.load(f)

            if not user:
                return

            st.session_state[self.KEY_LOGGED_IN] = True
            st.session_state[self.KEY_USER] = user
            st.session_state[self.KEY_USERNAME] = user.get("username", "Guest")

        except json.JSONDecodeError:
            logging.error("AUTH_FILE ist beschädigt (JSON ungültig)")
        except Exception:
            logging.exception("Unerwarteter Fehler beim Session-Restore")
