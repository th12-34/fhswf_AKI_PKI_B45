"""
Autor: Bastian Pivarcsi / Gregor Schumacher

Beschreibung:
Ermöglicht das Ändern von Profilinformationen unter Verwendung zentraler
Validierungsmethoden der Authentication-Klasse.

Quellen:
    - Vorwissen
    - ChatGPT 5.2
    - Lehrbrief "Python für alle"
"""

import streamlit as st
import time
from appconfig import KEY_USER
from databaseHandler import DatabaseAdministration
from authentication import Authentication


def _mask_secret(value: str, show_last: int = 4) -> str:
    """Maskiert ein Secret, um es abbilden zu können (zeigt niemals den ganzen Key)."""
    if not value:
        return "—"
    v = str(value).strip()
    if len(v) <= show_last:
        return "•" * len(v)
    return ("•" * (len(v) - show_last)) + v[-show_last:]


def show_profile_page():
    user = st.session_state.get(KEY_USER)
    if not user:
        st.warning("Bitte logge dich ein, um dein Profil einsehen zu können.")
        return

    db = DatabaseAdministration()
    auth = Authentication()

    username = user["username"]

    current_email = (user.get("email", "") or "").strip().lower()
    current_gemini_key = db.get_gemini_api_key(username) or ""

    st.subheader(f"Profil von {username}")
    status_container = st.container()

    # Infobereich
    info_c1, info_c2 = st.columns(2)
    with info_c1:
        st.write("**E-Mail**")
        st.write(current_email if current_email else "—")
    with info_c2:
        st.write("**Gemini API Key**")
        if current_gemini_key:
            st.write(f"Gesetzt ({_mask_secret(current_gemini_key)})")
        else:
            st.write("Nicht gesetzt")

    st.divider()

    # Benutzerinformationen ändern
    st.markdown("### Benutzerinformationen ändern")
    st.caption(
        "Nur Felder ausfüllen, die Sie wirklich ändern möchten. Leere Felder bleiben unverändert."
    )

    with st.form("edit_profile_form", clear_on_submit=True):
        new_email_input = (
            st.text_input("Neue E-Mail Adresse (optional)", value="").strip().lower()
        )
        new_gemini_key_input = st.text_input(
            "Neuer Gemini API Key (optional)", value="", type="password"
        ).strip()

        st.divider()
        st.write("**Passwort ändern (optional)**")
        new_password = st.text_input("Neues Passwort", type="password")
        confirm_password = st.text_input("Neues Passwort bestätigen", type="password")

        submit = st.form_submit_button("Änderungen speichern")

    if submit:
        has_error = False

        email_changed = bool(new_email_input) and (new_email_input != current_email)
        gemini_changed = bool(new_gemini_key_input)
        pw_changed = bool(new_password)

        pw_hash = None

        # Passwortchecks
        if pw_changed:
            if not confirm_password:
                status_container.error("Bitte bestätige das neue Passwort.")
                has_error = True
            elif new_password != confirm_password:
                status_container.error("Passwörter stimmen nicht überein!")
                has_error = True
            elif not auth.validate_password_strength(new_password):
                status_container.error("Passwort zu kurz (min. 6 Zeichen)!")
                has_error = True
            else:
                pw_hash = db.hash_password(new_password)

        # Emailchecks
        if email_changed and not has_error:
            if not auth.validate_email_syntax(new_email_input):
                status_container.error("Ungültiges E-Mail-Format!")
                has_error = True
            elif db.email_exists(new_email_input):
                status_container.error("Diese E-Mail ist bereits vergeben!")
                has_error = True

        if not has_error:
            # Keine Veränderung?
            if not (email_changed or gemini_changed or pw_changed):
                status_container.info("Keine Änderungen erkannt.")
            # Andernfalls Update der Benutzerinformationen
            else:
                final_email = new_email_input if email_changed else current_email
                final_gemini_key = (
                    new_gemini_key_input if gemini_changed else current_gemini_key
                )

                ok = db.update_user_settings(
                    username, final_email, pw_hash, final_gemini_key
                )
                if not ok:
                    status_container.error("Datenbankfehler beim Speichern.")
                else:
                    if email_changed:
                        st.session_state[KEY_USER]["email"] = final_email

                    if pw_changed:
                        status_container.success("Passwort geändert! Logout erfolgt.")
                        time.sleep(2)
                        auth.logout()
                        st.rerun()
                    else:
                        status_container.success("Profil aktualisiert!")
                        time.sleep(1)
                        st.rerun()

    # Benutzerkonto löschen
    st.write("")
    st.write("")
    with st.expander("Benutzerkonto löschen"):
        st.write("Vorgang ist endgültig!")
        if st.checkbox("Ich möchte mein Konto löschen."):
            if st.button("Konto jetzt löschen"):
                if db.delete_user_account(username):
                    auth.logout()
                    st.success("Konto gelöscht.")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Datenbankfehler beim Löschen des Kontos.")
