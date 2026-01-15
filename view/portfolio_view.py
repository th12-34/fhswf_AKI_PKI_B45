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
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

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

@st.cache_data(ttl=3600)
def get_historical_price_eur(symbol: str, currency: str, date_obj: datetime.date) -> float:
    """Holt historischen Preis und rechnet in EUR um."""
    try:
        # Zeitraum definieren (Datum + Puffer für Wochenende)
        start = date_obj
        end = date_obj + datetime.timedelta(days=4)
        
        # 1. Preis des Assets holen
        t = yf.Ticker(symbol)
        hist = t.history(start=start, end=end)
        
        if hist.empty:
            return None

        # Nimm den ersten verfügbaren Close-Wert im Zeitraum
        asset_price = hist['Close'].iloc[0]

        # 2. Währungskurs holen
        if currency == "EUR":
            return float(asset_price)
        
        # Wechselkurs historisch (Fallback auf aktuellen Kurs, wenn historisch nicht verfügbar)
        fx_symbol = f"{currency}EUR=X"
        fx_hist = yf.Ticker(fx_symbol).history(start=start, end=end)
        
        rate = fx_hist['Close'].iloc[0] if not fx_hist.empty else get_eur_exchange_rate(currency)
        return float(asset_price) * rate
    except:
        return None

@st.cache_data(ttl=600, show_spinner=False)
def calculate_portfolio_history(assets_data, period, interval):
    """
    Berechnet den historischen Verlauf des Portfolios basierend auf den aktuellen Beständen (Backtest).
    assets_data: Liste von Tupeln (symbol, amount, currency, type, bought_at)
    """
    if not assets_data:
        return None

    # 1. Symbole sammeln
    tickers = set()
    currencies = set()

    for sym, amt, cur, typ, bought_at in assets_data:
        if typ == 'cash':
            continue
        
        tickers.add(sym)
        if cur != 'EUR':
            currencies.add(cur)

    if not tickers:
        # Nur Cash vorhanden
        return None

    # 2. FX-Ticker definieren
    fx_map = {c: f"{c}EUR=X" for c in currencies}
    download_list = list(tickers) + list(fx_map.values())

    # 3. Daten laden
    try:
        raw_data = yf.download(download_list, period=period, interval=interval, progress=False)
        
        # Zugriff auf 'Close' Spalte sicherstellen
        if "Close" in raw_data:
            data = raw_data["Close"]
        else:
            data = raw_data # Fallback, falls nur 1 Ticker und keine Multi-Level-Columns

        # Wenn nur ein Ticker geladen wurde, ist es eine Series -> DataFrame konvertieren
        if isinstance(data, pd.Series):
            data = data.to_frame(name=download_list[0])
        
        # Lücken füllen
        data = data.ffill().bfill()

        # 4. Gesamtwert berechnen
        total_series = pd.Series(0.0, index=data.index)
        earliest_purchase = None

        for sym, amt, cur, typ, bought_at in assets_data:
            # Earliest Date tracken
            if bought_at:
                if earliest_purchase is None or bought_at < earliest_purchase:
                    earliest_purchase = bought_at

            # Start-Zeitpunkt für dieses Asset bestimmen
            start_ts = pd.Timestamp(bought_at) if bought_at else None
            if start_ts and data.index.tz is not None:
                start_ts = start_ts.tz_localize(data.index.tz)

            if typ == 'cash':
                if cur == 'EUR' and start_ts:
                    # Cash erst ab Kaufdatum addieren
                    total_series.loc[data.index >= start_ts] += amt
                continue
            
            if sym not in data.columns:
                continue

            price_series = data[sym]
            
            # Währungsumrechnung
            if cur != 'EUR' and cur in fx_map:
                fx_sym = fx_map[cur]
                if fx_sym in data.columns:
                    price_series = price_series * data[fx_sym]
            
            # Wert nur addieren, wenn Datum >= Kaufdatum
            if start_ts:
                # Wir nehmen eine Kopie, um das Original nicht zu verändern
                val_series = price_series * amt
                val_series.loc[data.index < start_ts] = 0.0
                total_series += val_series
            else:
                total_series += price_series * amt
            
        # 5. Graph erst ab dem ersten Kaufdatum anzeigen
        if earliest_purchase:
            start_ts_global = pd.Timestamp(earliest_purchase)
            if data.index.tz is not None:
                start_ts_global = start_ts_global.tz_localize(data.index.tz)
            total_series = total_series[total_series.index >= start_ts_global]

        return total_series

    except Exception as e:
        # st.error(f"Fehler bei Historienberechnung: {e}")
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

    # --- 2b. HISTORISCHER VERLAUF (NEU) ---
    if manager.currentPortfolio and manager.currentPortfolio.assets:
        st.markdown("### Portfolio Entwicklung")
        
        # UI Controls wie im Dashboard
        col_p, col_i = st.columns(2)
        with col_p:
            period = st.selectbox("Zeitraum", ["1mo", "3mo", "6mo", "1y", "ytd", "max"], index=3, key="port_hist_period")
        with col_i:
            interval = st.selectbox("Intervall", ["1d", "1wk", "1mo"], index=0, key="port_hist_interval")

        # Daten für Cache vorbereiten (Primitive Typen)
        assets_for_calc = [
            (a.symbol, a.amount, a.currency, a.type, a.bought_at) 
            for a in manager.currentPortfolio.assets
        ]

        with st.spinner("Berechne Portfolio-Historie..."):
            hist_series = calculate_portfolio_history(assets_for_calc, period, interval)

        if hist_series is not None and not hist_series.empty:
            # Performance Metriken
            end_val = hist_series.iloc[-1]
            invested_capital = manager.currentPortfolio.get_total_value()
            diff = end_val - invested_capital
            pct = (diff / invested_capital) * 100 if invested_capital != 0 else 0

            # Metrik anzeigen
            st.metric(
                label="Aktueller Gesamtwert",
                value=f"{end_val:,.2f} EUR",
                delta=f"{pct:.2f}% ({diff:,.2f} EUR)"
            )

            # Graph zeichnen
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(
                x=hist_series.index,
                y=hist_series.values,
                mode='lines',
                name='Portfolio Wert',
                line=dict(color='#00CC96', width=2),
                fill='tozeroy' # Optional: Fläche füllen
            ))

            fig_hist.update_layout(
                template="plotly_dark",
                height=350,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="",
                yaxis_title="Wert in EUR",
                hovermode="x unified"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            if len(assets_for_calc) > 0 and all(a[3] == 'cash' for a in assets_for_calc):
                 st.info("Historie für reine Cash-Portfolios nicht verfügbar.")
            else:
                 st.warning("Keine historischen Daten verfügbar.")

        # --- 2c. ASSET ALLOCATION (Tortendiagramm) ---
        st.markdown("### Investments")
        alloc_data = []
        for asset in manager.currentPortfolio.assets:
            # Preis ermitteln (Live oder Fallback auf Kaufpreis)
            price = asset.buy_price
            if asset.type != 'cash':
                live_data = fetch_live_data(asset.symbol)
                if live_data:
                    price = live_data['price_eur']
            val = asset.amount * price
            alloc_data.append({"Name": asset.name or asset.symbol, "Wert": val})
        
        if alloc_data:
            df_pie = pd.DataFrame(alloc_data)
            if not df_pie.empty and df_pie["Wert"].sum() > 0:
                fig_pie = px.pie(df_pie, values='Wert', names='Name', hole=0.4)
                fig_pie.update_traces(textinfo='percent+label')
                fig_pie.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        # --- 2d. AGGREGATED TABLE (Bestand) ---
        st.subheader("Bestand")
        
        # Aggregation der Assets
        holdings = {}
        for asset in manager.currentPortfolio.assets:
            if asset.type == 'cash':
                continue
            
            if asset.symbol not in holdings:
                holdings[asset.symbol] = {
                    "name": asset.name,
                    "type": asset.type,
                    "amount": 0.0,
                    "invested": 0.0
                }
            holdings[asset.symbol]["amount"] += asset.amount
            holdings[asset.symbol]["invested"] += (asset.amount * asset.buy_price)

        if holdings:
            # Daten für Sortierung vorbereiten
            holdings_list = []
            for sym, data in holdings.items():
                live_data = fetch_live_data(sym)
                current_price = live_data['price_eur'] if live_data else 0.0
                total_val = data["amount"] * current_price
                avg_buy_price = data["invested"] / data["amount"] if data["amount"] > 0 else 0.0
                
                holdings_list.append({
                    "sym": sym, "name": data["name"], "type": data["type"],
                    "amount": data["amount"], "current_price": current_price,
                    "avg_buy_price": avg_buy_price, "total_val": total_val
                })
            
            # Sortieren nach Gesamtwert absteigend
            holdings_list.sort(key=lambda x: x["total_val"], reverse=True)

            cols_i = st.columns([0.8, 2.0, 0.6, 0.8, 1, 1, 1.2])
            labels_i = ["Symbol", "Name", "Typ", "Menge", "Kurs", "Ø Kaufkurs", "Wert"]
            for col, label in zip(cols_i, labels_i):
                col.write(f"**{label}**")
            st.divider()

            for item in holdings_list:
                c = st.columns([0.8, 2.0, 0.6, 0.8, 1, 1, 1.2])
                c[0].write(item["sym"])
                c[1].write(item["name"])
                c[2].caption(item["type"].upper())
                c[3].write(f"{item['amount']:g}")
                c[4].write(f"{item['current_price']:,.2f} EUR" if item['current_price'] else "-")
                c[5].write(f"{item['avg_buy_price']:,.2f} EUR")
                c[6].write(f"**{item['total_val']:,.2f} EUR**")

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
                
                # Interaktive Eingabe ohne Formular, damit Datum den Preis aktualisieren kann
                st.write(f"Asset gefunden: **{data['name']}**")
                
                c1, c2 = st.columns(2)
                qty = c1.number_input("Menge", min_value=0.0, format="%.6f", key="asset_qty")
                
                # Auswahl: Aktueller Preis oder Historisch
                mode = c2.radio("Preis-Basis", ["Aktueller Kurs", "Historisches Datum"], horizontal=True)
                
                final_price = 0.0
                selected_date_str = datetime.date.today().strftime("%Y-%m-%d")

                if mode == "Aktueller Kurs":
                    final_price = data['price_eur']
                    st.number_input("Kaufpreis in EUR (Live)", value=final_price, disabled=True, format="%.2f", key="price_live")
                else:
                    sel_date = st.date_input("Kaufdatum", value=datetime.date.today(), max_value=datetime.date.today())
                    selected_date_str = sel_date.strftime("%Y-%m-%d")
                    with st.spinner("Lade historischen Kurs..."):
                        hist_price = get_historical_price_eur(data['symbol'], data['currency'], sel_date)
                    
                    if hist_price:
                        final_price = hist_price
                        st.number_input("Kaufpreis in EUR (Historisch)", value=final_price, disabled=True, format="%.2f", key="price_hist")
                    else:
                        st.error("Kein Kurs für dieses Datum gefunden.")

                if st.button("Asset hinzufügen", type="primary"):
                    if qty > 0 and final_price > 0:
                        new_asset = PortfolioAsset(selected_id, data['type'], data['symbol'], 
                                                   data['name'], float(qty), float(final_price), 
                                                   selected_date_str)
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
        with st.expander("Kaufhistorie", expanded=False):
            cols_h = st.columns([0.8, 1.5, 0.6, 0.8, 1, 1, 1, 1.2, 0.8])
            labels = ["Symbol", "Name", "Typ", "Menge", "Kurs", "Kaufkurs", "Datum", "Wert", "Aktion"]
            for col, label in zip(cols_h, labels):
                col.write(f"**{label}**")
            st.divider()

            for idx, asset in enumerate(manager.currentPortfolio.assets):
                c = st.columns([0.8, 1.5, 0.6, 0.8, 1, 1, 1, 1.2, 0.8])
                c[0].write(asset.symbol)
                c[1].write(asset.name)
                c[2].caption(asset.type.upper())
                c[3].write("-" if asset.type == "cash" else f"{asset.amount:g}")
                
                # Aktueller Kurs (Live)
                cur_price = "-"
                calc_price = asset.buy_price

                if asset.type != "cash":
                    live = fetch_live_data(asset.symbol)
                    if live:
                        calc_price = live['price_eur']
                        cur_price = f"{live['price_eur']:,.2f} EUR"
                c[4].write(cur_price)

                # Kaufkurs
                c[5].write("-" if asset.type == "cash" else f"{asset.buy_price:,.2f} EUR")
                c[6].write(asset.bought_at)
                
                # Gesamtwert
                current_val = asset.amount * calc_price
                c[7].write(f"**{current_val:,.2f} EUR**")
                if c[8].button("Loeschen", key=f"del_{idx}"):
                    manager.deleteAsset(asset.asset_id)
                    st.rerun()