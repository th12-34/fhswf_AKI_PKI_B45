"""
Seitenname: Portfolio-Verwaltung (Management)

Autor: 

Datum: 13.01.2026

Beschreibung:
Dieses Modul ermöglicht die übergeordnete Verwaltung der Portfolios. Nutzer können 
neue Portfolios benennen und erstellen sowie bestehende Portfolios inklusive 
aller darin enthaltenen Assets löschen. Es nutzt den PortfolioManager zur 
Kommunikation mit der Datenbank.


Quellen: 
- Programmierung
    - https://yfinance.yahoofinance.com/
"""

import datetime
import streamlit as st
import yfinance as yf
import pandas as pd

from databaseHandler import DatabaseAdministration
from portfoliomanager import Portfolio, PortfolioManager
from authentication import Authentication
from config import KEY_USER  # Zentrale Konstante nutzen

# Instanziierung der Datenbank- und Auth-Logik
ua = DatabaseAdministration()
auth = Authentication()

# --- Hauptansicht der Verwaltungsseite ---

def show_manage_page():
    """
    Stellt die UI für die Portfolio-Verwaltung bereit (Erstellen/Löschen).
    """
    # Login-Prüfung über Session State
    user = st.session_state.get(KEY_USER)
    if not user: 
        st.warning("Bitte logge dich ein, um deine Portfolios zu verwalten.")
        return

    # PortfolioManager für den aktuellen Nutzer initialisieren
    if "manager" not in st.session_state:
        st.session_state.manager = PortfolioManager(user["username"])
    
    manager = st.session_state.manager

    # --- 1. Bereich: Portfolio erstellen ---
    if "portfolio_success" in st.session_state:
        st.success(st.session_state.portfolio_success)
        del st.session_state.portfolio_success

    with st.expander("➕ Neues Portfolio erstellen"):
        new_portfolio_name = st.text_input("Name des neuen Portfolios", placeholder="z.B. Altersvorsorge")
        if st.button("Portfolio anlegen"):
            if new_portfolio_name:
                # Erstellt Portfolio in der DB
                manager.createPortfolio(new_portfolio_name)
                st.session_state.portfolio_success = f"Portfolio '{new_portfolio_name}' wurde erfolgreich erstellt!"
                st.rerun()
            else:
                st.error("Bitte gib einen gültigen Namen für das Portfolio ein.")
    
    st.divider()

    # --- 2. Bereich: Portfolios anzeigen und löschen ---
    st.subheader("Deine Portfolios")

    portfolios = manager.getPortfolios()
    
    if not portfolios:
        st.info("Du hast aktuell noch keine Portfolios angelegt.")
    else:
        # Tabellen-Header für die Übersicht
        h1, h2, h3 = st.columns([1, 8, 1])
        h1.markdown("**ID**")
        h2.markdown("**Name**")
        h3.markdown("**Löschen**")

        # Auflistung der Portfolios
        for portfolio_id, name in portfolios:
            c1, c2, c3 = st.columns([1, 8, 1])
            c1.write(portfolio_id)
            c2.write(name)

            # Lösch-Button mit eindeutigem Key pro Portfolio
            if c3.button("🗑️", key=f"del_port_{portfolio_id}"):
                # Manager löscht das Portfolio aus der Datenbank (inkl. CASCADE Assets)
                if manager.deletePortfolio(portfolio_id):
                    st.rerun()