import streamlit as st
from databaseHandler import DatabaseAdministration


def get_useradministration() -> DatabaseAdministration:
    if "bkv" not in st.session_state:
        st.session_state.bkv = DatabaseAdministration("user.db")
    return st.session_state.bkv


def show_register_page():
    bkv = get_useradministration()

    st.title("🧾 Registrierung")
    if st.button("⬅️ Zurück zum Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
    st.write("Bitte erstelle dir hier ein neues Benutzerkonto:")

    username = st.text_input("Benutzername")
    email = st.text_input("E-Mail")
    passwort = st.text_input("Passwort", type="password")
    passwort2 = st.text_input("Passwort wiederholen", type="password")

    if st.button("Konto anlegen"):
        if not username or not email or not passwort or not passwort2:
            st.error("Bitte alle Felder ausfüllen.")
        elif passwort != passwort2:
            st.error("Die Passwörter stimmen nicht überein.")
        elif len(passwort) < 6:
            st.error("Das Passwort sollte mindestens 6 Zeichen lang sein.")
        else:
            if bkv.username_exisist(username):
                st.error("Benutzername ist bereits vergeben.")
            elif bkv.email_exists(email):
                st.error("Es existiert bereits ein Konto mit dieser E-Mail.")
            else:
                ok = bkv.add_user(username, email, passwort)
                if ok:
                    st.success("Konto erfolgreich angelegt! 🎉 Du kannst dich jetzt einloggen.")
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("Beim Anlegen des Kontos ist ein Fehler aufgetreten.")
                

