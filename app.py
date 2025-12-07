import streamlit as st
from register_page import show_register_page
from dashboard import show_dashboard
from navbar import render_top_navbar

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

    if "selected_symbol" not in st.session_state:
        st.session_state["selected_symbol"] = None
    if "data" not in st.session_state:
        st.session_state["data"] = None

    


    page = st.session_state.page
    # Haupt-App-Fluss
    render_top_navbar()


    if page == "dashboard":
        show_dashboard()

    elif page == "register_page":
        show_register_page()
    


if __name__ == "__main__":
    main()
