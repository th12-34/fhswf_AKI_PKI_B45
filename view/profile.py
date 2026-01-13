"""
Programmname: Benutzerprofil (Profile Page)
Autor: Bastian Pivarcsi
Datum: 13.01.2026
Beschreibung:
Ermöglicht das Ändern von Profilinformationen unter Verwendung zentraler 
Validierungsmethoden der Authentication-Klasse.
"""

import streamlit as st
import time
from appconfig import KEY_USER
from databaseHandler import DatabaseAdministration
from authentication import Authentication

def show_profile_page():
    st.header("Benutzereinstellungen")
    
    user = st.session_state.get(KEY_USER)
    if not user:
        st.warning("Bitte logge dich ein.")
        return

    db = DatabaseAdministration()
    auth = Authentication()
    
    username = user["username"]
    current_email = user.get("email", "")
    current_gemini_key = db.get_gemini_api_key(username)

    st.subheader(f"Profil von {username}")
    status_container = st.container()
    
    with st.form("edit_profile_form"):
        new_email = st.text_input("E-Mail Adresse", value=current_email).strip().lower()
        new_gemini_key = st.text_input("Gemini API Key", value=current_gemini_key, type="password")
        
        st.divider()
        st.write("**Passwort ändern**")
        new_password = st.text_input("Neues Passwort", type="password")
        confirm_password = st.text_input("Neues Passwort bestätigen", type="password")
        
        submit = st.form_submit_button("Änderungen speichern")

        if submit:
            # 1. Syntax-Check über zentrale Funktion
            if not auth.validate_email_syntax(new_email):
                st.error("Ungültiges E-Mail-Format!")
                return
            
            # 2. Dubletten-Check (nur wenn E-Mail geändert wurde)
            if new_email != current_email and db.email_exists(new_email):
                st.error("Diese E-Mail ist bereits vergeben!")
                return

            # 3. Passwort-Check über zentrale Funktion
            pw_hash = None
            if new_password:
                if not auth.validate_password_strength(new_password):
                    st.error("Passwort zu kurz (min. 6 Zeichen)!")
                    return
                if new_password != confirm_password:
                    st.error("Passwörter stimmen nicht überein!")
                    return
                pw_hash = db.hash_password(new_password)

            # 4. Speichern
            if db.update_user_settings(username, new_email, pw_hash, new_gemini_key):
                if new_password:
                    status_container.success("Passwort geändert! Logout erfolgt...")
                    time.sleep(2)
                    auth.logout()
                    st.rerun()
                else:
                    st.session_state[KEY_USER]["email"] = new_email
                    status_container.success("Profil aktualisiert!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Datenbankfehler beim Speichern.")

    st.divider()
    with st.expander("Löschen Benutzerkonto"):
        st.write("Vorgang ist endgültig!")
        if st.checkbox("Ich möchte mein Konto löschen."):
            if st.button("Konto jetzt löschen"):
                if db.delete_user_account(username):
                    auth.logout()
                    st.success("Konto gelöscht.")
                    time.sleep(2)
                    st.rerun()