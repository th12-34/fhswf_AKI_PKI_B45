"""
Seitenname: Portfolio-Ansicht
Autor:
Datum: 14.01.2026
Seitenname: Portfolioverwaltung (Management)
Beschreibung: Verwaltung der Portfolios mit fortlaufender Nummerierung und ohne Icons.
"""

import datetime
import streamlit as st
import pandas as pd
import time

from databaseHandler import DatabaseAdministration
from portfoliomanager import PortfolioManager
from appconfig import KEY_USER


def show_manage_page():
    """
    Stellt die UI für die Portfolio-Verwaltung bereit (Erstellen/Löschen).
    """
    user = st.session_state.get(KEY_USER)
    if not user:
        st.warning("Bitte logge dich ein, um dein Portfolio zu verwalten.")
        return

    if "manager" not in st.session_state:
        st.session_state.manager = PortfolioManager(user["username"])

    manager = st.session_state.manager

    # --- 1. Bereich: Portfolio erstellen ---
    st.write("")
    with st.expander("Neues Portfolio erstellen", expanded=False):
        new_portfolio_name = st.text_input(
            "Name des neuen Portfolios", placeholder="z.B. Altersvorsorge"
        )
        if st.button("Portfolio anlegen"):
            if new_portfolio_name:
                manager.createPortfolio(new_portfolio_name)
                st.success(f"Portfolio '{new_portfolio_name}' wurde erstellt!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Bitte gib einen Namen ein.")

    st.write("")
    # --- 2. Bereich: Portfolios anzeigen und löschen ---
    st.subheader("Übersicht deiner angelegten Portfolios")

    portfolios = manager.getPortfolios()

    if not portfolios:
        st.info("Du hast aktuell noch keine Portfolios angelegt.")
    else:
        # Tabellen-Header (Nr. statt ID)
        h1, h2, h3 = st.columns([1, 7, 2])
        h1.markdown("**Nr.**")
        h2.markdown("**Name**")
        h3.markdown("**Aktion**")
        st.divider()

        # Auflistung der Portfolios mit enumerate für fortlaufende Nummern
        # i ist der Zähler (start=1), portfolio_id ist der DB-Key für die Logik
        for i, (portfolio_id, name) in enumerate(portfolios, start=1):
            c1, c2, c3 = st.columns([1, 7, 2])

            # Anzeige der laufenden Nummer
            c1.write(f"{i}.")

            # Anzeige des Namens
            c2.write(f"**{name}**")

            # Lösch-Button (Text statt Icon)
            if c3.button("Löschen", key=f"del_port_{portfolio_id}"):
                if manager.deletePortfolio(portfolio_id):
                    # Cache bereinigen falls nötig (siehe vorheriger Turn)
                    if "manager" in st.session_state:
                        st.session_state.manager = PortfolioManager(user["username"])
                    st.rerun()
