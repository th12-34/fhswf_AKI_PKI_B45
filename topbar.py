import streamlit as st
from authentication import Authentication

# Setzt direkt bei Instanziierung Default-Werte
auth = Authentication()

def _render_auth_messages_for(auth: Authentication, action: str) -> None:
    """
    Guard-Clause: Zeigt auth_error/auth_info direkt unter dem Formular an,
    aber nur wenn dieses Formular zuletzt submitted wurde.
    """
    if st.session_state.get("last_auth_action") != action:
        return

    err, info = auth.consume_messages()

    if err:
        st.error(err)
    elif info:
        st.info(info)

def render_topbar():

    title = st.session_state["page_key"]

    st.session_state.setdefault("auth_tab", "Login")

    left, right = st.columns([8, 2], vertical_alignment="center")

    with left:
        st.markdown(f"## {title}")

    with right:
        logged_in = st.session_state.get(Authentication.KEY_LOGGED_IN, False)
        username = st.session_state.get(Authentication.KEY_USERNAME, "Guest")

        if "show_snow" not in st.session_state:
            st.session_state["show_snow"] = False

        """    if "auth_tab" not in st.session_state:
            st.session_state["auth_tab"] = "login"  # default """

        with st.popover(f"{username}", icon="👤"):

            if logged_in:
                if st.session_state["show_snow"]:
                    st.snow()
                    st.session_state["show_snow"] = False  # nur einmal

                st.write(f"Willkommen **{username}**")
                if st.button("Logout"):
                    auth.logout()
                    st.session_state["show_snow"] = False
                    st.rerun()
                return

            # mit st.tabs kein Event st.rerun wenn man zwischen Tabs wechselt, st.error st.info bleiben bestehen
            #tab_login, tab_register = st.tabs(["Login", "Registration"])
            tab = st.segmented_control(
                "auth_tab_selector",
                options=["Login", "Registration"],
                key="auth_tab",
                label_visibility="collapsed",
                #on_change=_clear_auth_ui_state,
                args=(auth,),
            )
            # Login Tab
            #with tab_login:
            if tab == "Login":
                username = st.text_input("User", key="login_user")
                password = st.text_input("Passwort", type="password", key="login_pw")
                if st.button("Login"):
                    st.session_state["last_auth_action"] = "login"
                    user = auth.login(username, password)
                    if user:
                        st.session_state["show_snow"] = True
                        st.rerun()
                _render_auth_messages_for(auth, "login")
                pass
            # Register Tab
            #with tab_register:
            else:
                rusername = st.text_input(
                    "Benutzername", 
                    key="reg_user",
                    help="Mindestens 3 Zeichen. Keine Leerzeichen."
                    )
                remail = st.text_input(
                    "E-Mail", 
                    key="reg_email",
                    help="Beispiel: name@domain.de"
                    )
                rpassword = st.text_input(
                    "Passwort", 
                    type="password", 
                    key="reg_pw",
                    help="Mindestens 6 Zeichen."
                    )
                if st.button("Neuen Account erstellen"):
                    st.session_state["last_auth_action"] = "register"
                    auth.register(rusername, remail, rpassword)
                    st.rerun()
                _render_auth_messages_for(auth, "register")
            pass

def _render_login_form():
    """Render the login form for users to log in."""
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Benutzername")  
        password = st.text_input("Passwort", type="password")  
        submitted = st.form_submit_button("Einloggen")  

        if submitted:
            user = auth.login(username, password) 
            if user:
                st.success("Erfolgreich eingeloggt!")  
                st.session_state.page = "dashboard"  
                st.rerun()
            else:
                st.error("Ungültige Anmeldedaten")
