"""
Programmname: Hauptseitenverwaltung

Autor: Bastian Pivarcsi / Maximilian Pfau

Datum: 13.01.2026

Beschreibung:
Zentrales Einstiegsskript für die Streamlit-Applikation. Verwaltet die Seitennavigation,
die Authentifizierungswiederherstellung und das Layout der Topbar.

Quellen:
- Programmierung
    - Lehrbrief zur Vorlesung
    - https://docs.streamlit.io/develop/api-reference/navigation/st.page st.navigation
    - ChatGPT 5.2
"""

import streamlit as st
from topbar import render_topbar
from view.dashboard import show_dashboard
from view.portfolio_view import show_view_page
from view.portfolios_manage import show_manage_page
from view.profile import show_profile_page
from authentication import Authentication

# --- Konfiguration ---
st.set_page_config(
    page_title="Mein Finanz-Dashboard", layout="wide", initial_sidebar_state="expanded"
)

# CSS zur Optimierung des Headers und Paddings
# Damit könnte man den Header mit den Default Streamlit Optionen oben rechts deaktiveren, dann kann man aber die seitliche Navigationsleiste nicht mehr aufklappen
st.markdown(
    """
<style>
header[data-testid="stHeader"] {
    height: 0px;
    visibility: hidden;
}
header[data-testid="stHeader"] * {
    visibility: visible;
}
.block-container {
    padding-top: 1rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# --- Page Wrapper Funktionen ---


def dashboard_page():
    st.session_state["page_key"] = "Marktanalyse"
    render_topbar()
    show_dashboard()


def portfolios_manage_page():
    st.session_state["page_key"] = "Portfolioverwaltung"
    render_topbar()
    show_manage_page()


def portfolio_view_page():
    st.session_state["page_key"] = "Portfolioübersicht"
    render_topbar()
    show_view_page()


def profile_page():
    """Wrapper für die Benutzereinstellungen."""
    st.session_state["page_key"] = "Benutzereinstellungen"
    render_topbar()
    show_profile_page()


# --- Hauptprogramm ---


def main():
    # Nach Start / Reload prüfen, ob bereits eine Session aktiv ist
    auth = Authentication()
    auth.restore_session()

    pages = {
        "Recherche": [
            st.Page(dashboard_page, title="Marktanalyse", url_path="dashboard"),
        ],
        "Portfolio": [
            st.Page(portfolio_view_page, title="Übersicht", url_path="portfolio-view"),
            st.Page(portfolios_manage_page, title="Verwaltung", url_path="portfolio-manager"),
        ],
        "Profil": [
            st.Page(profile_page, title="Benutzereinstellungen", url_path="profile"),
        ],
    }

    # Navigation initialisieren und ausführen
    pg = st.navigation(pages, position="sidebar")
    pg.run()


if __name__ == "__main__":
    main()
