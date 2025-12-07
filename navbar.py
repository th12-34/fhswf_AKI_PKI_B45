import streamlit as st
from authentication import Authentication
from dashboard import show_dashboard

auth = Authentication()

def render_top_navbar():
    """Render the top navigation bar with login/logout functionality."""

    user = auth.get_logged_in_user()

    with st.container():
        st.markdown(
            """
            <style>
                .topbar-container {
                    padding: 0.5rem 0;
                    border-bottom: 1px solid #444;
                }
            </style>
            """,
            unsafe_allow_html=True
        )

        _, _, top_col3 = st.columns([2, 3, 2])  

        with top_col3:
            if user:
                _render_logged_in_user(user)
            else:
                _render_login_form()
                if st.button("Registrieren"):
                    st.session_state.page = "register_page" 
                    st.rerun()


def _render_logged_in_user(user):
    """Render the logged-in user details and logout button."""
    st.markdown(f"**👤 {user['username']}**")
    if st.button("Logout"):
        auth.logout()  
        st.session_state.page = "dashboard" 


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