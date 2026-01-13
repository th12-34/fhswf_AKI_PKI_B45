"""
Seitenname: Portfolio-Ansicht

Autor: 

Datum: 13.01.2026

Beschreibung:
Dieses Modul verwaltet die visuelle Darstellung der Nutzer-Portfolios. Es bietet
Funktionen zum Suchen und Hinzufügen von Assets, zur automatischen Währungsumrechnung
in Euro (via Yahoo Finance FX-Rates) und zur tabellarischen Übersicht der Bestände.


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

# Instanziierung der benötigten Klassen
ua = DatabaseAdministration()
auth = Authentication()

# --- Hilfsfunktionen für Datenabruf und Umrechnung ---

def _fetch_yf_name(symbol: str) -> str | None:
    """Ruft den Klarnamen eines Wertpapiers von Yahoo Finance ab."""
    try:
        ticker = yf.Ticker(symbol)
        info = getattr(ticker, "info", {}) or {}
        return info.get("shortName") or info.get("longName")
    except Exception:
        return None

def _get_ticker_currency(symbol: str) -> str | None:
    """Liefert die Handelswährung des Symbols (z.B. 'USD', 'EUR')."""
    try:
        t = yf.Ticker(symbol)
        info = getattr(t, "info", {}) or {}
        return info.get("currency")
    except Exception:
        return None

def _convert_to_eur(price: float, currency: str, d: datetime.date) -> float | None:
    """
    Rechnet einen Preis von einer Fremdwährung in EUR um.
    Nutzt historische Wechselkurse zum Zeitpunkt des Kaufdatums.
    """
    currency = currency.upper()
    if currency == "EUR":
        return price

    pair = f"{currency}EUR=X"   # Währungspaar für FX-Kurs

    try:
        end = d + datetime.timedelta(days=1)
        start = d - datetime.timedelta(days=7)

        data = yf.download(pair, start=start, end=end, interval="1d", progress=False)

        if data is None or data.empty:
            return None

        # Zeitzonen entfernen für Vergleichbarkeit
        if isinstance(data.index, pd.DatetimeIndex) and data.index.tz is not None:
            data.index = data.index.tz_convert(None)

        target = datetime.datetime.combine(d, datetime.time(0, 0))
        data_before = data[data.index <= target]

        rate = float(data_before["Close"].iloc[-1]) if not data_before.empty else float(data["Close"].iloc[0])
        return price * rate
    except Exception:
        return None

def _infer_asset_type(symbol: str, quote_type: str | None = None) -> str:
    """Bestimmt automatisch, ob es sich um eine Aktie oder Kryptowährung handelt."""
    if quote_type:
        qt = quote_type.lower()
        if "crypto" in qt or qt == "cryptocurrency":
            return "crypto"
        if qt in ("equity", "etf", "mutualfund", "index", "fund"):
            return "stock"

    s = symbol.upper()
    crypto_suffixes = ("-USD", "-USDT", "-EUR", "-BTC")
    if s.endswith(crypto_suffixes) or s in {"BTC", "ETH", "SOL", "XRP", "ADA", "DOGE"}:
        return "crypto"
    return "stock"

def _fetch_price_for_date(symbol: str, d: datetime.date) -> float | None:
    """Ruft den historischen Schlusskurs eines Symbols für ein bestimmtes Datum ab."""
    try:
        end = d + datetime.timedelta(days=1)
        start = d - datetime.timedelta(days=30)
        data = yf.download(symbol, start=start, end=end, interval="1d", progress=False)

        if data is None or data.empty:
            return None

        if isinstance(data.index, pd.DatetimeIndex) and data.index.tz is not None:
            data.index = data.index.tz_convert(None)

        target = datetime.datetime.combine(d, datetime.time(0, 0))
        data_before = data[data.index <= target]

        return float(data_before["Close"].iloc[-1]) if not data_before.empty else float(data["Close"].iloc[0])
    except Exception:
        return None

# --- Hauptansicht ---

def show_view_page():
    """Rendert die Portfolio-Übersicht und die Verwaltung der Assets."""
    
    # Nutzerprüfung
    user = st.session_state.get(KEY_USER)
    if not user: 
        st.warning("Bitte logge dich ein.")
        return

    # Portfolio-Manager initialisieren
    if "manager" not in st.session_state:
        st.session_state.manager = PortfolioManager(user["username"])
    
    manager = st.session_state.manager

    # Portfolios des Nutzers laden
    portfolios = manager.getPortfolios()
    if not portfolios:
        st.info("Keine Portfolios gefunden. Bitte erstelle zuerst ein Portfolio.")
        return

    # Auswahl-UI
    labels = [f"{p[0]} – {p[1]}" for p in portfolios]
    id_by_label = {label: p[0] for label, p in zip(labels, portfolios)}

    selected_label = st.selectbox("Wähle ein Portfolio", labels)
    selected_portfolio_id = id_by_label[selected_label]
    
    manager.selectPortfolioId(selected_portfolio_id)

    # Anzeige des Gesamtwerts
    if manager.currentPortfolio:
        total_val = manager.currentPortfolio.get_total_value()
        st.metric("Gesamtwert (EUR)", f"{total_val:,.2f} €")

    # --- Bereich: Asset hinzufügen ---
    with st.expander("Neues Asset hinzufügen", expanded=False):

        if "reset_nonce" not in st.session_state:
            st.session_state["reset_nonce"] = 0

        query = st.text_input("Suche nach Aktie oder Krypto", key=f"asset_search_query_{st.session_state.reset_nonce}")
        selected_symbol = None

        if "show_form" not in st.session_state:
            st.session_state["show_form"] = False
        
        def reset_all():
            """Setzt die Eingabemaske nach erfolgreichem Hinzufügen zurück."""
            keys_to_pop = ["asset_symbol_input", "amount_input", "price_mode_input", 
                           "manual_price_input", "date_input", "asset_choice"]
            for k in keys_to_pop:
                st.session_state.pop(k, None)
            st.session_state.show_form = False
            st.session_state.reset_nonce += 1
            st.rerun()

        # Suchlogik
        if query:
            try:
                result = yf.Search(query, max_results=5)
                options = [f"{q['symbol']} – {q.get('shortname', 'N/A')}" for q in result.quotes]
                if options:
                    choice = st.selectbox("Vorschläge", ["--- Bitte wählen ---"] + options)
                    if choice != "--- Bitte wählen ---":
                        selected_symbol = choice.split(" – ")[0]
                        st.session_state["asset_symbol_input"] = selected_symbol
                        st.session_state["show_form"] = True
            except Exception as e:
                st.error(f"Suche fehlgeschlagen: {e}")

        # Formular-Anzeige
        if st.session_state["show_form"]:
            with st.form("add_asset_form"):
                asset_symbol_val = st.text_input("Symbol", key="asset_symbol_input")
                amount_val = st.number_input("Menge", min_value=0.0, step=0.01, key="amount_input")
                date = st.date_input("Kaufdatum", value=datetime.date.today(), key="date_input")
                preis_modus = st.radio("Preisermittlung", ["Automatisch", "Manuell"], key="price_mode_input")
                manual_price = st.number_input("Preis pro Einheit (EUR)", min_value=0.0, key="manual_price_input")
                
                submit = st.form_submit_button("Hinzufügen")

                if submit:
                    if not asset_symbol_val or amount_val <= 0:
                        st.error("Bitte Symbol und Menge prüfen.")
                    else:
                        # Preis-Logik (Auto/Manuell)
                        if preis_modus == "Automatisch":
                            price_in_ccy = _fetch_price_for_date(asset_symbol_val, date)
                            ccy = _get_ticker_currency(asset_symbol_val) or "EUR"
                            price_eur = _convert_to_eur(price_in_ccy, ccy, date)                
                        else:
                            price_eur = manual_price

                        if price_eur:
                            from portfolioasset import PortfolioAsset
                            new_asset = PortfolioAsset(
                                portfolio_id=selected_portfolio_id,
                                asset_type=_infer_asset_type(asset_symbol_val),
                                asset_symbol=asset_symbol_val,
                                asset_name=_fetch_yf_name(asset_symbol_val),
                                amount=amount_val,
                                buy_price=price_eur,
                                bought_at=date.strftime("%Y-%m-%d")
                            )
                            
                            if manager.addAssetToPortfolio(new_asset):
                                st.success(f"{asset_symbol_val} erfolgreich hinzugefügt!")
                                reset_all()
                            else:
                                st.error("Fehler beim Speichern in der Datenbank.")
                        else:
                            st.error("Preis konnte nicht ermittelt werden (Netzwerkfehler?).")
    
    st.divider()

    # --- Bereich: Übersichtstabelle ---
    st.subheader("Aktuelle Assets")

    if manager.currentPortfolio and manager.currentPortfolio.assets:
        # Tabellen-Header
        header = st.columns([1, 2, 1, 1, 1, 1])
        headers = ["Symbol", "Name", "Typ", "Menge", "Preis (EUR)", "Aktion"]
        for col, h_text in zip(header, headers):
            col.markdown(f"**{h_text}**")
        st.divider()

        # Zeilenweise Anzeige
        for asset in manager.currentPortfolio.assets:
            cols = st.columns([1, 2, 1, 1, 1, 1])
            cols[0].write(asset.symbol)
            cols[1].write(asset.name or "-")
            cols[2].caption(asset.type)
            cols[3].write(f"{asset.amount}")
            cols[4].write(f"{asset.buy_price:.2f} €")
            
            # Löschfunktion über Button-Key-Bindung
            if cols[5].button("🗑️", key=f"del_{asset.asset_id}"):
                if manager.deleteAsset(asset.asset_id):
                    st.rerun()
    else:
        st.info("Noch keine Assets in diesem Portfolio.")