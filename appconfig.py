"""
Autor: Bastian Pivarcsi

Beschreibung:
Zentrale Konfigurationsdatei für Session-State-Keys und globale
Einstellungen, um Konsistenz über alle Module hinweg zu gewährleisten.
"""

# Session State Keys
KEY_LOGGED_IN = "logged_in"
KEY_USERNAME = "username"
KEY_USER = "user"
KEY_AUTH_ERROR = "auth_error"
KEY_AUTH_INFO = "auth_info"

# Dateipfade
AUTH_FILE = "auth.json"
DATABASE_NAME = "user.db"
