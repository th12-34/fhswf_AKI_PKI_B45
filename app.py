import streamlit as st
from register_page import show_register_page
from dashboard import show_dashboard
from navbar import render_top_navbar

# 1. Konfiguration der Seite (Titel, Layout, Dark Mode initialisieren)
st.set_page_config(page_title="Mein Finanz-Dashboard", layout="wide", initial_sidebar_state="expanded")

def main():
   # Standardseite
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    # 1. Top-Navigation immer oben rendern
    render_top_navbar()

    # 2. Routing: welche Seite wird gezeigt?
    page = st.session_state.page

    if page == "dashboard":
        show_dashboard()
    elif page == "register":
        show_register_page()


if __name__ == "__main__":
    main()
