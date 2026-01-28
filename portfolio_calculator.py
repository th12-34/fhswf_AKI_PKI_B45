"""
Modul: Portfolio Calculator
Autor: Maxim Sein
Datum: 16.01.2026
Beschreibung: Enthält die Logik für Finanzberechnungen, API-Abrufe (yfinance), 
Währungsumrechnungen und Sortierung der Bestände. Dient als Service-Layer für die Portfolio-View.

Quellen:
- Programmierung
    - https://yfinance.yahoofinance.com/
    - https://docs.streamlit.io/
    - Lehrbrief zur Vorlesung
    - Gemini
"""

import datetime
import streamlit as st
import yfinance as yf
import pandas as pd


class PortfolioCalculator:
    """
    Klasse für finanzmathematische Berechnungen und Datenabruf.
    Methoden sind statisch, um einfache Nutzung und Caching zu ermöglichen.
    """

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_eur_exchange_rate(from_currency: str):
        """Holt den aktuellen Wechselkurs zu EUR. Fallback ist 1.0."""
        if not from_currency or from_currency == "EUR":
            return 1.0

        # Sonderfall britische Pence
        if from_currency == "GBp":
            try:
                rate = yf.Ticker("GBPEUR=X").history(period="1d")["Close"].iloc[-1]
                return rate / 100
            except:
                return 0.011  # Grober Fallback

        try:
            ticker_symbol = f"{from_currency}EUR=X"
            rate = yf.Ticker(ticker_symbol).history(period="1d")["Close"].iloc[-1]
            return rate
        except:
            return 1.0

    @staticmethod
    @st.cache_data(ttl=600)
    def fetch_live_data(symbol: str):
        """
        Ruft Marktdaten ab. Versucht bei Krypto automatisch -EUR anzuhaengen.
        Nutzt Fallbacks, falls .info fehlschlaegt.
        """
        if not symbol:
            return None

        search_symbol = symbol.strip().upper()
        # Automatisches Fix fuer bekannte Kryptos ohne Paar
        if search_symbol in ["BTC", "ETH", "SOL", "XRP", "ADA"]:
            search_symbol = f"{search_symbol}-EUR"

        try:
            ticker = yf.Ticker(search_symbol)
            info = ticker.info

            # Preis-Ermittlung mit mehreren Fallbacks (wichtig fuer BTC)
            price = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or info.get("previousClose")
            )

            if price is None:
                # Wenn .info leer ist (oft bei Krypto), nutze history
                hist = ticker.history(period="1d")
                if not hist.empty:
                    price = hist["Close"].iloc[-1]

            if price is None:
                return None

            currency = info.get("currency", "EUR")
            # Aufruf der eigenen statischen Methode
            rate = PortfolioCalculator.get_eur_exchange_rate(currency)
            price_in_eur = float(price) * rate

            # Typ-Zuordnung
            raw_type = info.get("quoteType", "").upper()
            if (
                raw_type == "CRYPTOCURRENCY"
                or "-EUR" in search_symbol
                or "-USD" in search_symbol
            ):
                a_type = "crypto"
            else:
                a_type = "stock"

            return {
                "name": info.get("shortName") or info.get("longName") or search_symbol,
                "price_eur": float(price_in_eur),
                "type": a_type,
                "currency": currency,
                "symbol": search_symbol,
            }
        except:
            return None

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_historical_price_eur(
        symbol: str, currency: str, date_obj: datetime.date
    ) -> float:
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
            asset_price = hist["Close"].iloc[0]

            # 2. Währungskurs holen
            if currency == "EUR":
                return float(asset_price)

            # Wechselkurs historisch (Fallback auf aktuellen Kurs, wenn historisch nicht verfügbar)
            fx_symbol = f"{currency}EUR=X"
            fx_hist = yf.Ticker(fx_symbol).history(start=start, end=end)

            rate = (
                fx_hist["Close"].iloc[0]
                if not fx_hist.empty
                else PortfolioCalculator.get_eur_exchange_rate(currency)
            )
            return float(asset_price) * rate
        except:
            return None

    @staticmethod
    @st.cache_data(ttl=600, show_spinner=False)
    def calculate_portfolio_history(assets_data, period, interval):
        """
        Berechnet den historischen Verlauf des Portfolios basierend auf den aktuellen Beständen (Backtest).
        assets_data: Liste von Tupeln (symbol, amount, currency, type, bought_at, buy_price)
        """
        if not assets_data:
            return None

        # 1. Symbole sammeln
        tickers = set()
        currencies = set()

        for sym, amt, cur, typ, bought_at, buy_price in assets_data:
            if typ == "cash":
                continue

            tickers.add(sym)
            if cur != "EUR":
                currencies.add(cur)

        if not tickers:
            # Nur Cash vorhanden
            return None

        # 2. FX-Ticker definieren
        fx_map = {c: f"{c}EUR=X" for c in currencies}
        download_list = list(tickers) + list(fx_map.values())

        # 3. Daten laden
        try:
            raw_data = yf.download(
                download_list, period=period, interval=interval, progress=False
            )

            # Zugriff auf 'Close' Spalte sicherstellen
            if "Close" in raw_data:
                data = raw_data["Close"]
            else:
                data = (
                    raw_data  # Fallback, falls nur 1 Ticker und keine Multi-Level-Columns
                )

            # Wenn nur ein Ticker geladen wurde, ist es eine Series -> DataFrame konvertieren
            if isinstance(data, pd.Series):
                data = data.to_frame(name=download_list[0])

            # Lücken füllen
            data = data.ffill().bfill()

            # 4. Gesamtwert berechnen
            total_series = pd.Series(0.0, index=data.index)
            invested_series = pd.Series(0.0, index=data.index)
            earliest_purchase = None

            for sym, amt, cur, typ, bought_at, buy_price in assets_data:
                # Earliest Date tracken
                if bought_at:
                    if earliest_purchase is None or bought_at < earliest_purchase:
                        earliest_purchase = bought_at

                # Start-Zeitpunkt für dieses Asset bestimmen
                start_ts = pd.Timestamp(bought_at) if bought_at else None
                if start_ts and data.index.tz is not None:
                    start_ts = start_ts.tz_localize(data.index.tz)

                # Investiertes Kapital (buy_price ist in EUR)
                invested_val = amt * buy_price

                if typ == "cash":
                    if cur == "EUR" and start_ts:
                        # Cash erst ab Kaufdatum addieren
                        total_series.loc[data.index >= start_ts] += amt
                        invested_series.loc[data.index >= start_ts] += invested_val
                    continue

                if sym not in data.columns:
                    continue

                price_series = data[sym]

                # Währungsumrechnung
                if cur != "EUR" and cur in fx_map:
                    fx_sym = fx_map[cur]
                    if fx_sym in data.columns:
                        price_series = price_series * data[fx_sym]

                # Wert nur addieren, wenn Datum >= Kaufdatum
                if start_ts:
                    # Wir nehmen eine Kopie, um das Original nicht zu verändern
                    val_series = price_series * amt
                    val_series.loc[data.index < start_ts] = 0.0
                    total_series += val_series
                    invested_series.loc[data.index >= start_ts] += invested_val
                else:
                    total_series += price_series * amt
                    invested_series += invested_val

            return pd.DataFrame({"Total": total_series, "Invested": invested_series})

        except Exception as e:
            # st.error(f"Fehler bei Historienberechnung: {e}")
            return None

    @staticmethod
    def calculate_performance(invested: float, current_value: float):
        """
        Berechnet die absolute und prozentuale Entwicklung.
        """
        diff = current_value - invested
        pct = (diff / invested) * 100 if invested != 0 else 0.0
        return diff, pct

    @staticmethod
    def calculate_period_profit(hist_df, current_total_val, current_invested_val):
        """
        Berechnet die Veränderung des Gewinns im Zeitraum (absolut und relativ zum Invest).
        """
        if hist_df is None or hist_df.empty:
            return 0.0, 0.0

        # Profit zu Beginn des Zeitraums
        start_profit = hist_df['Total'].iloc[0] - hist_df['Invested'].iloc[0]

        # Profit am Ende (Aktuell)
        end_profit = current_total_val - current_invested_val

        profit_change_abs = end_profit - start_profit
        profit_change_rel = (profit_change_abs / current_invested_val * 100) if current_invested_val != 0 else 0.0

        return profit_change_abs, profit_change_rel

    @staticmethod
    def get_aggregated_holdings(assets):
        """
        Gruppiert Assets nach Symbol, berechnet Durchschnittspreise und Gesamtwert.
        Gibt eine sortierte Liste zurück.
        """
        holdings = {}
        for asset in assets:
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

        results = []
        for sym, data in holdings.items():
            live_data = PortfolioCalculator.fetch_live_data(sym)
            current_price = live_data["price_eur"] if live_data else 0.0
            total_val = data["amount"] * current_price
            avg_buy_price = (
                data["invested"] / data["amount"] if data["amount"] > 0 else 0.0
            )

            results.append({
                "sym": sym,
                "name": data["name"],
                "type": data["type"],
                "amount": data["amount"],
                "current_price": current_price,
                "avg_buy_price": avg_buy_price,
                "total_val": total_val,
                "invested": data["invested"],
            })

        # Sortieren nach Gesamtwert absteigend
        results.sort(key=lambda x: x["total_val"], reverse=True)
        return results