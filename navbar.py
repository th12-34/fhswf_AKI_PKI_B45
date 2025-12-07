import streamlit as st
from authentication import Authentication
from dashboard import show_dashboard

auth = Authentication()

def render_top_navbar():
    """Render the top navigation bar with login/logout functionality."""

    if "page" not in st.session_state:
        st.session_state.page = "dashboard"


    user = auth.get_logged_in_user()

    # Render the top navigation bar
    with st.container():
        # Add some spacing and styling
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

        # Create columns for layout
        _, _, top_col3 = st.columns([2, 3, 2])  

        # Render login/logout section
        with top_col3:
            if user:
                _render_logged_in_user(user)
            else:
                _render_login_form()

            
                if st.button("Registrieren"):
                    st.session_state.page = "register_page"  # Redirect to register page
                    st.rerun()


def _render_logged_in_user(user):
    """Render the logged-in user details and logout button."""
    st.markdown(f"**👤 {user['username']}**")  # Display the username
    if st.button("Logout"):
        auth.logout()  # Log out the user
        st.session_state.page = "dashboard"  # Set the page to dashboard
        st.rerun()


def _render_login_form():
    """Render the login form for users to log in."""
    st.markdown("Nicht eingeloggt")  # Display "Not logged in" message

    # Create a form for login
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Benutzername")  # Username input
        password = st.text_input("Passwort", type="password")  # Password input
        submitted = st.form_submit_button("Einloggen")  # Submit button


        if submitted:
            user = auth.login(username, password)  # Attempt to log in
            if user:
                st.success("Erfolgreich eingeloggt!")  # Success message
                st.session_state.page = "dashboard"  # Set the page to dashboard
                st.rerun()
            else:
                st.error("Ungültige Anmeldedaten")  # Error message