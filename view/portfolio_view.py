"""
Seitenname: Portfolio-Ansicht
Autor: Bastian Pivarcsi
Datum: 14.01.2026
Beschreibung: Portfolioverwaltung Barmittel, Aktien und Wertpapiere
"""

import datetime
import streamlit as st
import yfinance as yf
import time

# Eigene Module
from portfoliomanager import PortfolioManager
from portfolioasset import PortfolioAsset
import appconfig as config 

# --- WÄHRUNGS- & API-LOGIK ---

@st.cache_data(ttl=3600)
def get_eur_exchange_rate(from_currency: str):
    """Holt den aktuellen Wechselkurs zu EUR. Fallback ist 1.0."""
    if not from_currency or from_currency == "EUR":
        return 1.0
    
    # Sonderfall britische Pence
    if from_currency == "GBp":
        try:
            rate = yf.Ticker("GBPEUR=X").history(period="1d")['Close'].iloc[-1]
            return rate / 100
        except: return 0.011 # Grober Fallback
    
    try:
        ticker_symbol = f"{from_currency}EUR=X"
        rate = yf.Ticker(ticker_symbol).history(period="1d")['Close'].iloc[-1]
        return rate
    except:
        return 1.0

@st.cache_data(ttl=600)
def fetch_live_data(symbol: str):
    """
    Ruft Marktdaten ab. Versucht bei Krypto automatisch -EUR anzuhaengen.
    Nutzt Fallbacks, falls .info fehlschlaegt.
    """
    if not symbol: return None
    
    search_symbol = symbol.strip().upper()
    # Automatisches Fix fuer bekannte Kryptos ohne Paar
    if search_symbol in ["BTC", "ETH", "SOL", "XRP", "ADA"]:
        search_symbol = f"{search_symbol}-EUR"

    try:
        ticker = yf.Ticker(search_symbol)
        info = ticker.info
        
        # Preis-Ermittlung mit mehreren Fallbacks (wichtig fuer BTC)
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        
        if price is None:
            # Wenn .info leer ist (oft bei Krypto), nutze history
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
        
        if price is None: return None
            
        currency = info.get("currency", "EUR")
        rate = get_eur_exchange_rate(currency)
        price_in_eur = float(price) * rate

        # Typ-Zuordnung
        raw_type = info.get("quoteType", "").upper()
        if raw_type == "CRYPTOCURRENCY" or "-EUR" in search_symbol or "-USD" in search_symbol:
            a_type = "crypto"
        else:
            a_type = "stock"

        return {
            "name": info.get("shortName") or info.get("longName") or search_symbol,
            "price_eur": float(price_in_eur),
            "type": a_type,
            "currency": currency,
            "symbol": search_symbol
        }
    except:
        return None

def show_view_page():
    user = st.session_state.get(config.KEY_USER)
    if not user: 
        st.warning("Bitte anmelden.")
        return

    if "manager" not in st.session_state:
        st.session_state.manager = PortfolioManager(user["username"])
    
    manager = st.session_state.manager
    portfolios = manager.getPortfolios()
    
    if not portfolios:
        st.title("Portfolio Bestaende")
        return

    # --- 2. HEADER & PORTFOLIO-WAHL ---
    st.title("Portfolio Verwaltung")
    id_to_label_map = {p[0]: f"{i}. {p[1]}" for i, p in enumerate(portfolios, start=1)}
    
    selected_id = st.selectbox(
        "Portfolio waehlen",
        options=list(id_to_label_map.keys()),
        format_func=lambda x: id_to_label_map[x]
    )
    
    manager.selectPortfolioId(selected_id)
    total_val = manager.currentPortfolio.get_total_value() if manager.currentPortfolio else 0.0
    st.metric("Gesamtwert", f"{total_val:,.2f} EUR")
    st.divider()

    # --- 3. EINGABEMASKE ---
    tab_assets, tab_cash = st.tabs(["Wertpapiere und Krypto", "Barmittel"])

    with tab_assets:
        query = st.text_input("Ticker-Symbol (z.B. BTC, MSTR, AAPL)", key="search_input").strip()
        if query:
            data = fetch_live_data(query)
            if data:
                # Info-Box bei Umrechnung
                if data['currency'] != "EUR":
                    st.info(f"Originalwaehrung: {data['currency']}. Der Preis wurde automatisch in EUR umgerechnet.")
                
                with st.form("add_asset_f", clear_on_submit=True):
                    st.write(f"Asset gefunden: **{data['name']}**")
                    c1, c2 = st.columns(2)
                    qty = c1.number_input("Menge", min_value=0.0, format="%.6f")
                    price = c2.number_input("Kaufpreis in EUR", value=data['price_eur'], format="%.2f")
                    
                    if st.form_submit_button("Speichern", use_container_width=True):
                        if qty > 0:
                            new_asset = PortfolioAsset(selected_id, data['type'], data['symbol'], 
                                                       data['name'], float(qty), float(price), 
                                                       datetime.date.today().strftime("%Y-%m-%d"))
                            manager.addAssetToPortfolio(new_asset)
                            st.success("Erfolgreich hinzugefuegt.")
                            time.sleep(0.5)
                            st.rerun()
            else:
                st.error("Symbol konnte nicht gefunden werden. Bitte Ticker prüfen.")

    with tab_cash:
        with st.form("c_form", clear_on_submit=True):
            val = st.number_input("Euro-Betrag", min_value=0.0)
            if st.form_submit_button("Barmittel buchen"):
                cash_asset = PortfolioAsset(selected_id, "cash", "EUR", "Barmittel", float(val), 1.0, datetime.date.today().strftime("%Y-%m-%d"))
                manager.addAssetToPortfolio(cash_asset)
                st.rerun()

    # --- 4. TABELLE ---
    if manager.currentPortfolio and manager.currentPortfolio.assets:
        st.subheader("Aktuelle Positionen")
        cols_h = st.columns([0.8, 1.5, 0.7, 1, 1, 1, 1.2, 0.8])
        labels = ["Symbol", "Name", "Typ", "Menge", "Kurs", "Datum", "Wert", "Aktion"]
        for col, label in zip(cols_h, labels):
            col.write(f"**{label}**")
        st.divider()

        for idx, asset in enumerate(manager.currentPortfolio.assets):
            c = st.columns([0.8, 1.5, 0.7, 1, 1, 1, 1.2, 0.8])
            c[0].write(asset.symbol)
            c[1].write(asset.name)
            c[2].caption(asset.type.upper())
            c[3].write("-" if asset.type == "cash" else f"{asset.amount:g}")
            c[4].write("-" if asset.type == "cash" else f"{asset.buy_price:,.2f} EUR")
            c[5].write(asset.bought_at)
            c[6].write(f"**{asset.get_total_value():,.2f} EUR**")
            if c[7].button("Loeschen", key=f"del_{idx}"):
                manager.deleteAsset(asset.asset_id)
                st.rerun()