"""
Programmname: UI_Components

Autor: Maximilian Pfau

Datum: 13.01.2026

Beschreibung:
Diese Modul enthält die UI-Komponenten für die Streamlit-Oberfläche, insbesondere
die Topbar mit integrierter Login- und Registrierungslogik sowie das Handling
von Statusmeldungen.


Quellen:
- Programmierung
    - Lehrbrief zur Vorlesung
    - https://docs.streamlit.io/develop/api-reference/widgets/st.popover
    - ChatGPT 5.2
"""

import streamlit as st
from authentication import Authentication
import appconfig as appconfig

# Setzt direkt bei Instanziierung Default-Werte
auth = Authentication()


def _render_auth_messages_for(auth: Authentication, action: str) -> None:
    """
    Zeigt auth_error/auth_info direkt unter dem Formular an,
    falls dieses Formular zuletzt abgeschickt wurde.

    :param auth: Instanz der Authentication-Klasse
    :param action: Kennung der Aktion (login/register)
    :return: -
    """
    if st.session_state.get("last_auth_action") != action:
        return

    err, info = auth.consume_messages()

    if err:
        st.error(err)
    elif info:
        st.info(info)


def render_topbar():
    """
    Rendert die obere Navigationsleiste inklusive Nutzer-Menü (Popover).

    :param: -
    :return: -
    """
    title = st.session_state.get("page_key", "Dashboard")
    st.session_state.setdefault("auth_tab", "Login")

    left, right = st.columns([8, 2], vertical_alignment="center")

    with left:
        st.markdown(f"## {title}")

    with right:
        logged_in = st.session_state.get(appconfig.KEY_LOGGED_IN, False)
        username = st.session_state.get(appconfig.KEY_USERNAME, "Gast")

        if "show_snow" not in st.session_state:
            st.session_state["show_snow"] = False

        with st.popover(f"{username}", icon="👤"):
            if logged_in:
                if st.session_state["show_snow"]:
                    st.snow()
                    st.session_state["show_snow"] = False

                st.write(f"Willkommen **{username}**")
                if st.button("Logout"):
                    auth.logout()
                    st.session_state["show_snow"] = False
                    st.rerun()
                return

            # Auswahl zwischen Login und Registrierung
            tab = st.segmented_control(
                "auth_tab_selector",
                options=["Login", "Registrierung"],
                key="auth_tab",
                label_visibility="collapsed",
            )

            # Login Bereich
            if tab == "Login":
                l_user = st.text_input("User", key="login_user")
                l_pw = st.text_input("Passwort", type="password", key="login_pw")
                if st.button("Login"):
                    st.session_state["last_auth_action"] = "login"
                    user = auth.login(l_user, l_pw)
                    if user:
                        st.session_state["show_snow"] = True
                        st.rerun()
                _render_auth_messages_for(auth, "login")

            # Registrierung Bereich
            else:
                rusername = st.text_input(
                    "Benutzername",
                    key="reg_user",
                    help="Mindestens 3 Zeichen. Keine Leerzeichen.",
                )
                remail = st.text_input(
                    "E-Mail", key="reg_email", help="Beispiel: name@domain.de"
                )
                rpassword = st.text_input(
                    "Passwort",
                    type="password",
                    key="reg_pw",
                    help="Mindestens 6 Zeichen.",
                )
                # NEU: Eingabefeld für den Gemini API Key
                rgemini = st.text_input(
                    "Gemini API Key",
                    type="password",
                    key="reg_gemini",
                    help="Dein persönlicher API Key von Google AI Studio.",
                )

                if st.button("Neuen Account erstellen"):
                    st.session_state["last_auth_action"] = "register"
                    # Aufruf der erweiterten Register-Funktion
                    success = auth.register(rusername, remail, rpassword, rgemini)
                    if success:
                        st.rerun()

                _render_auth_messages_for(auth, "register")
