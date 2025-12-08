import streamlit as st
from register_page import show_register_page
from dashboard import show_dashboard
from navbar import render_top_navbar
from portfolio_page import show_add_assets_page   # <-- NEU

st.set_page_config(page_title="Mein Finanz-Dashboard", layout="wide", initial_sidebar_state="expanded")

def main():

    st.title("Finanzen")
    if "selected_symbol" not in st.session_state:
        st.session_state["selected_symbol"] = None
    if "data" not in st.session_state:
        st.session_state["data"] = None

    if "page" not in st.session_state:
        st.session_state["headerTitel"] = "Finanzübersicht"
        st.session_state.page = "dashboard"
        st.session_state['show_login_form'] = False

    page = st.session_state.page

    # Navbar (inkl. Login, Navigation etc.)
    render_top_navbar()

    # Page-Routing
    if page == "dashboard":
        show_dashboard()
    elif page == "register_page":
        show_register_page()
    elif page == "add_assets":              # <-- NEU
        show_add_assets_page()


if __name__ == "__main__":
    main()
