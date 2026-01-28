"""
Seitenname: Portfolioübersicht
Autor: Bastian Pivarcsi, Maxim Sein
Datum: 14.01.2026
Beschreibung: Portfolioverwaltung Barmittel, Aktien und Wertpapiere
"""

import datetime
import streamlit as st
import time
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Eigene Module
from portfoliomanager import PortfolioManager
from portfolioasset import PortfolioAsset
from portfolio_calculator import PortfolioCalculator
from search import render_ticker_search
import appconfig as config


def show_view_page():
    user = st.session_state.get(config.KEY_USER)
    if not user:
        st.warning("Bitte logge dich ein, um dein Portfolio einsehen zu können.")
        return

    if "manager" not in st.session_state:
        st.session_state.manager = PortfolioManager(user["username"])

    manager = st.session_state.manager
    portfolios = manager.getPortfolios()

    if not portfolios:
        st.title("Portfolio Bestaende")
        return

    # --- 2. HEADER & PORTFOLIO-WAHL ---
    id_to_label_map = {p[0]: f"{i}. {p[1]}" for i, p in enumerate(portfolios, start=1)}

    selected_id = st.selectbox(
        "Portfolioauswahl",
        options=list(id_to_label_map.keys()),
        format_func=lambda x: id_to_label_map[x],
    )

    manager.selectPortfolioId(selected_id)

    # --- 2b. HISTORISCHER VERLAUF (NEU) ---
    if manager.currentPortfolio and manager.currentPortfolio.assets:
        st.markdown("### Entwicklung des ausgewählten Portfolios")

        # UI Controls wie im Dashboard
        col_p, col_i = st.columns(2)
        with col_p:
            period = st.selectbox(
                "Zeitraum",
                ["1mo", "3mo", "6mo", "1y", "ytd", "max"],
                index=3,
                key="port_hist_period",
            )
        with col_i:
            interval = st.selectbox(
                "Intervall", ["1d", "1wk", "1mo"], index=0, key="port_hist_interval"
            )

        # Daten für Cache vorbereiten (Primitive Typen)
        assets_for_calc = [
            (a.symbol, a.amount, a.currency, a.type, a.bought_at, a.buy_price)
            for a in manager.currentPortfolio.assets
        ]

        with st.spinner("Berechne Portfolio-Historie..."):
            hist_df = PortfolioCalculator.calculate_portfolio_history(assets_for_calc, period, interval)

        # Fallback: Wenn Assets vorhanden sind (hist_series ist nicht None), aber leer (z.B. Kauf heute),
        # oder der letzte Wert 0 ist (Kauf heute, Historie endet gestern), fügen wir den aktuellen Wert hinzu.
        # Aktuellen Marktwert berechnen:
        holdings = PortfolioCalculator.get_aggregated_holdings(manager.currentPortfolio.assets)
        market_val = sum(h['total_val'] for h in holdings)
        cash_val = sum(a.amount for a in manager.currentPortfolio.assets if a.type == 'cash')
        total_now = market_val + cash_val
        invested_now = manager.currentPortfolio.get_total_value()

        if hist_df is not None and (hist_df.empty or (hist_df['Total'].iloc[-1] == 0 and total_now > 0)):
            if total_now > 0:
                now_df = pd.DataFrame({"Total": [total_now], "Invested": [invested_now]}, index=[pd.Timestamp.now()])
                if hist_df.empty:
                    hist_df = now_df
                else:
                    hist_df = pd.concat([hist_df, now_df])

        if hist_df is not None and not hist_df.empty:
            # Performance Metriken
            end_val = total_now
            invested_capital = invested_now
            diff, pct = PortfolioCalculator.calculate_performance(invested_capital, end_val)

            # Zeitraum-Performance (Absoluter Gewinn)
            # Gewinn = Total - Invested
            hist_df['Profit'] = hist_df['Total'] - hist_df['Invested']
            
            start_profit = hist_df['Profit'].iloc[0]
            end_profit = end_val - invested_capital

            profit_change = end_profit - start_profit

            # Metrik anzeigen
            c1, c2, c3 = st.columns(3)
            c1.metric(
                label="Aktueller Gesamtwert",
                value=f"{end_val:,.2f} EUR",
                delta=f"{pct:.2f}% ({diff:,.2f} EUR)",
            )
            c2.metric(label=f"Gewinn ({period})", value=f"{profit_change:,.2f} EUR")
            c3.metric(label="Datenpunkte", value=len(hist_df))

            # Graph zeichnen
            fig_hist = go.Figure()
            fig_hist.add_trace(
                go.Scatter(
                    x=hist_df.index,
                    y=hist_df['Total'],
                    mode="lines" if len(hist_df) > 1 else "markers",
                    name="Portfolio Wert",
                    line=dict(color="#00CC96", width=2),
                    fill="tozeroy",  # Optional: Fläche füllen
                )
            )

            fig_hist.update_layout(
                template="plotly_dark",
                height=350,
                margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="",
                yaxis_title="Wert in EUR",
                hovermode="x unified",
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            if len(assets_for_calc) > 0 and all(
                a[3] == "cash" for a in assets_for_calc
            ):
                st.info("Historie für reine Cash-Portfolios nicht verfügbar.")
            else:
                st.warning("Keine historischen Daten verfügbar.")

        # --- 2c. ASSET ALLOCATION (Tortendiagramm) ---
        st.markdown("### Investments")
        alloc_data = []
        for asset in manager.currentPortfolio.assets:
            # Preis ermitteln (Live oder Fallback auf Kaufpreis)
            price = asset.buy_price
            if asset.type != "cash":
                live_data = PortfolioCalculator.fetch_live_data(asset.symbol)
                if live_data:
                    price = live_data["price_eur"]
            val = asset.amount * price
            alloc_data.append({"Name": asset.name or asset.symbol, "Wert": val})

        if alloc_data:
            df_pie = pd.DataFrame(alloc_data)
            if not df_pie.empty and df_pie["Wert"].sum() > 0:
                fig_pie = px.pie(df_pie, values="Wert", names="Name", hole=0.4)
                fig_pie.update_traces(textinfo="percent+label")
                fig_pie.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_pie, use_container_width=True)

        # --- 2d. AGGREGATED TABLE (Bestand) ---
        st.subheader("Bestand")

        # Aggregation und Sortierung der Bestände
        holdings_list = PortfolioCalculator.get_aggregated_holdings(manager.currentPortfolio.assets)

        if holdings_list:

            cols_i = st.columns([0.8, 2.0, 0.6, 0.8, 1, 1, 1.2, 1.0])
            labels_i = ["Symbol", "Name", "Typ", "Menge", "Kurs", "Ø Kaufkurs", "Wert", "Entwicklung"]
            for col, label in zip(cols_i, labels_i):
                col.write(f"**{label}**")
            st.divider()

            for item in holdings_list:
                c = st.columns([0.8, 2.0, 0.6, 0.8, 1, 1, 1.2, 1.0])
                c[0].write(item["sym"])
                c[1].write(item["name"])
                c[2].caption(item["type"].upper())
                c[3].write(f"{item['amount']:.1f}")
                c[4].write(
                    f"{item['current_price']:,.2f} EUR"
                    if item["current_price"]
                    else "-"
                )
                c[5].write(f"{item['avg_buy_price']:,.2f} EUR")
                c[6].write(f"**{item['total_val']:,.2f} EUR**")

                # Entwicklung berechnen
                invested = item["invested"]
                diff, pct = PortfolioCalculator.calculate_performance(invested, item["total_val"])
                color = "green" if diff >= 0 else "red"
                prefix = "+" if diff >= 0 else ""
                c[7].markdown(f":{color}[{prefix}{pct:.2f}%]")

    st.divider()

    # --- 3. EINGABEMASKE ---
    tab_assets, tab_cash = st.tabs(["Wertpapiere und Krypto", "Barmittel"])

    with tab_assets:
        # Nutzung der ausgelagerten Such-Logik
        found_symbol = render_ticker_search(key_prefix="port_add", label="Ticker-Suche (z.B. Apple, BTC)")
        
        if found_symbol:
            data = PortfolioCalculator.fetch_live_data(found_symbol)
            if data:
                # Info-Box bei Umrechnung
                if data["currency"] != "EUR":
                    st.info(
                        f"Originalwaehrung: {data['currency']}. Der Preis wurde automatisch in EUR umgerechnet."
                    )

                # Interaktive Eingabe ohne Formular, damit Datum den Preis aktualisieren kann
                st.write(f"Asset gefunden: **{data['name']}**")

                c1, c2 = st.columns(2)
                qty = c1.number_input(
                    "Menge", min_value=0.0, format="%.1f", key="asset_qty"
                )

                # Auswahl: Aktueller Preis oder Historisch
                mode = c2.radio(
                    "Preis-Basis",
                    ["Aktueller Kurs", "Historisches Datum"],
                    horizontal=True,
                )

                final_price = 0.0
                selected_date_str = datetime.date.today().strftime("%Y-%m-%d")

                if mode == "Aktueller Kurs":
                    final_price = data["price_eur"]
                    st.number_input(
                        "Kaufpreis in EUR (Live)",
                        value=final_price,
                        disabled=True,
                        format="%.2f",
                        key="price_live",
                    )
                else:
                    sel_date = st.date_input(
                        "Kaufdatum",
                        value=datetime.date.today(),
                        max_value=datetime.date.today(),
                    )
                    selected_date_str = sel_date.strftime("%Y-%m-%d")
                    with st.spinner("Lade historischen Kurs..."):
                        hist_price = PortfolioCalculator.get_historical_price_eur(
                            data["symbol"], data["currency"], sel_date
                        )

                    if hist_price:
                        final_price = hist_price
                        st.number_input(
                            "Kaufpreis in EUR (Historisch)",
                            value=final_price,
                            disabled=True,
                            format="%.2f",
                            key="price_hist",
                        )
                    else:
                        st.error("Kein Kurs für dieses Datum gefunden.")

                if st.button("Asset hinzufügen", type="primary"):
                    if qty > 0 and final_price > 0:
                        new_asset = PortfolioAsset(
                            selected_id,
                            data["type"],
                            data["symbol"],
                            data["name"],
                            float(qty),
                            float(final_price),
                            selected_date_str,
                        )
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
                cash_asset = PortfolioAsset(
                    selected_id,
                    "cash",
                    "EUR",
                    "Barmittel",
                    float(val),
                    1.0,
                    datetime.date.today().strftime("%Y-%m-%d"),
                )
                manager.addAssetToPortfolio(cash_asset)
                st.rerun()

    # --- 4. TABELLE ---
    if manager.currentPortfolio and manager.currentPortfolio.assets:
        with st.expander("Kaufhistorie", expanded=False):
            cols_h = st.columns([0.8, 1.5, 0.6, 0.8, 1, 1, 1, 1.2, 0.8])
            labels = [
                "Symbol",
                "Name",
                "Typ",
                "Menge",
                "Kurs",
                "Kaufkurs",
                "Datum",
                "Wert",
                "Aktion",
            ]
            for col, label in zip(cols_h, labels):
                col.write(f"**{label}**")
            st.divider()

            # Sortieren nach Kaufdatum absteigend (neueste oben)
            sorted_assets = sorted(
                manager.currentPortfolio.assets,
                key=lambda x: x.bought_at,
                reverse=True
            )

            for idx, asset in enumerate(sorted_assets):
                c = st.columns([0.8, 1.5, 0.6, 0.8, 1, 1, 1, 1.2, 0.8])
                c[0].write(asset.symbol)
                c[1].write(asset.name)
                c[2].caption(asset.type.upper())
                c[3].write("-" if asset.type == "cash" else f"{asset.amount:.1f}")

                # Aktueller Kurs (Live)
                cur_price = "-"
                calc_price = asset.buy_price

                if asset.type != "cash":
                    live = PortfolioCalculator.fetch_live_data(asset.symbol)
                    if live:
                        calc_price = live["price_eur"]
                        cur_price = f"{live['price_eur']:,.2f} EUR"
                c[4].write(cur_price)

                # Kaufkurs
                c[5].write(
                    "-" if asset.type == "cash" else f"{asset.buy_price:,.2f} EUR"
                )
                c[6].write(asset.bought_at)

                # Gesamtwert
                current_val = asset.amount * calc_price
                c[7].write(f"**{current_val:,.2f} EUR**")
                if c[8].button("Löschen", key=f"del_{idx}"):
                    manager.deleteAsset(asset.asset_id)
                    st.rerun()
