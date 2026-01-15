"""
Seitenname: Portfolio-Ansicht
Autor: Bastian Pivarcsi
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
import appconfig as config


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
        format_func=lambda x: id_to_label_map[x],
    )

    manager.selectPortfolioId(selected_id)

    # --- 2b. HISTORISCHER VERLAUF (NEU) ---
    if manager.currentPortfolio and manager.currentPortfolio.assets:
        st.markdown("### Portfolio Entwicklung")

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
            (a.symbol, a.amount, a.currency, a.type, a.bought_at)
            for a in manager.currentPortfolio.assets
        ]

        with st.spinner("Berechne Portfolio-Historie..."):
            hist_series = PortfolioCalculator.calculate_portfolio_history(assets_for_calc, period, interval)

        if hist_series is not None and not hist_series.empty:
            # Performance Metriken
            end_val = hist_series.iloc[-1]
            invested_capital = manager.currentPortfolio.get_total_value()
            diff, pct = PortfolioCalculator.calculate_performance(invested_capital, end_val)

            # Metrik anzeigen
            st.metric(
                label="Aktueller Gesamtwert",
                value=f"{end_val:,.2f} EUR",
                delta=f"{pct:.2f}% ({diff:,.2f} EUR)",
            )

            # Graph zeichnen
            fig_hist = go.Figure()
            fig_hist.add_trace(
                go.Scatter(
                    x=hist_series.index,
                    y=hist_series.values,
                    mode="lines",
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

        # Aggregation der Assets
        holdings = {}
        for asset in manager.currentPortfolio.assets:
            if asset.type == "cash":
                continue

            if asset.symbol not in holdings:
                holdings[asset.symbol] = {
                    "name": asset.name,
                    "type": asset.type,
                    "amount": 0.0,
                    "invested": 0.0,
                }
            holdings[asset.symbol]["amount"] += asset.amount
            holdings[asset.symbol]["invested"] += asset.amount * asset.buy_price

        if holdings:
            # Daten für Sortierung vorbereiten
            holdings_list = []
            for sym, data in holdings.items():
                live_data = PortfolioCalculator.fetch_live_data(sym)
                current_price = live_data["price_eur"] if live_data else 0.0
                total_val = data["amount"] * current_price
                avg_buy_price = (
                    data["invested"] / data["amount"] if data["amount"] > 0 else 0.0
                )

                holdings_list.append(
                    {
                        "sym": sym,
                        "name": data["name"],
                        "type": data["type"],
                        "amount": data["amount"],
                        "current_price": current_price,
                        "avg_buy_price": avg_buy_price,
                        "total_val": total_val,
                        "invested": data["invested"],
                    }
                )

            # Sortieren nach Gesamtwert absteigend
            holdings_list.sort(key=lambda x: x["total_val"], reverse=True)

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
        query = st.text_input(
            "Ticker-Symbol (z.B. BTC, MSTR, AAPL)", key="search_input"
        ).strip()
        if query:
            data = PortfolioCalculator.fetch_live_data(query)
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
                if c[8].button("Loeschen", key=f"del_{idx}"):
                    manager.deleteAsset(asset.asset_id)
                    st.rerun()
