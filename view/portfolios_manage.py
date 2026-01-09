import datetime
import streamlit as st
import yfinance as yf
import pandas as pd

from databaseHandler import DatabaseAdministration
from portfoliomanager import Portfolio, PortfolioManager
from authentication import Authentication


ua = DatabaseAdministration()
auth = Authentication()


def _fetch_yf_name(symbol: str) -> str | None:
    try:
        ticker = yf.Ticker(symbol)
        info = getattr(ticker, "info", {}) or {}
        return info.get("shortName") or info.get("longName")
    except Exception:
        return None

def _get_ticker_currency(symbol: str) -> str | None:
    """
    Liefert die Handelswährung des Symbols laut yfinance, z.B. 'USD', 'EUR', 'CHF'.
    """
    try:
        t = yf.Ticker(symbol)
        info = getattr(t, "info", {}) or {}
        return info.get("currency")
    except Exception:
        return None


def _convert_to_eur(price: float, currency: str, d: datetime.date) -> float | None:
    """
    Rechnet price in 'currency' nach EUR um.
    Nutzt FX-Ticker wie 'USDEUR=X', 'CHFEUR=X' etc.
    Gibt None zurück, wenn kein Kurs gefunden wird.
    """
    currency = currency.upper()
    if currency == "EUR":
        return price

    pair = f"{currency}EUR=X"   # z.B. USDEUR=X, CHFEUR=X

    try:
        end = d + datetime.timedelta(days=1)
        start = d - datetime.timedelta(days=7)

        data = yf.download(
            pair,
            start=start,
            end=end,
            interval="1d",
            progress=False,
        )

        if data is None or data.empty:
            return None

        if isinstance(data.index, pd.DatetimeIndex) and data.index.tz is not None:
            data.index = data.index.tz_convert(None)

        target = datetime.datetime.combine(d, datetime.time(0, 0))
        data_before = data[data.index <= target]

        if not data_before.empty:
            rate = float(data_before["Close"].iloc[-1])
        else:
            rate = float(data["Close"].iloc[0])

        return price * rate
    except Exception:
        return None



def _infer_asset_type(symbol: str, quote_type: str | None = None) -> str:
    if quote_type:
        qt = quote_type.lower()
        if "crypto" in qt or qt == "cryptocurrency":
            return "crypto"
        if qt in ("equity", "etf", "mutualfund", "index", "fund"):
            return "stock"

    s = symbol.upper()
    crypto_suffixes = ("-USD", "-USDT", "-EUR", "-BTC")
    if s.endswith(crypto_suffixes):
        return "crypto"
    common_crypto = {"BTC", "ETH", "SOL", "XRP", "ADA", "DOGE"}
    if s in common_crypto:
        return "crypto"
    return "stock"


def _fetch_price_for_date(symbol: str, d: datetime.date) -> float | None:
    try:
        end = d + datetime.timedelta(days=1)
        start = d - datetime.timedelta(days=30)

        data = yf.download(
            symbol,
            start=start,
            end=end,
            interval="1d",
            progress=False,
        )

        if data is None or data.empty:
            return None

        if isinstance(data.index, pd.DatetimeIndex) and data.index.tz is not None:
            data.index = data.index.tz_convert(None)

        target = datetime.datetime.combine(d, datetime.time(0, 0))
        data_before = data[data.index <= target]

        if not data_before.empty:
            return float(data_before["Close"].iloc[-1])

        return float(data["Close"].iloc[0])
    except Exception:
        return None


def show_manage_page():
    
    user = st.session_state.get(Authentication.KEY_USER)
    if not user: 
        st.warning("Bitte logge dich ein.")
        return

    # Manager initialisieren
    if "manager" not in st.session_state:
        st.session_state.manager = PortfolioManager(user["username"])
    
    manager = st.session_state.manager

    # --- 1. Portfolio erstellen ---

    if "portfolio_success" in st.session_state:
        st.success(st.session_state.portfolio_success)
        del st.session_state.portfolio_success

    with st.expander("Neues Portfolio erstellen"):
        new_portfolio_name = st.text_input("Name des neuen Portfolios")
        if st.button("Erstellen"):
            if new_portfolio_name:
                manager.createPortfolio(new_portfolio_name)
                st.session_state.portfolio_success = f"Portfolio '{new_portfolio_name}' wurde erstellt!"
                st.rerun()
            else:
                st.error("Bitte gib einen Namen ein.")
    
    st.divider()

    # --- 2. Portfolios anzeigen / löschen ---
    st.subheader("Portfolios")

    portfolios = manager.getPortfolios()
    if not portfolios:
        st.info("Keine Portfolios gefunden!")
    else:
        # Header
        h1, h2, h3 = st.columns([1, 8, 1])
        h1.markdown("**ID**")
        h2.markdown("**Name**")
        h3.markdown("**Aktion**")

        # Rows
        for portfolio_id, name in portfolios:
            c1, c2, c3 = st.columns([1, 8, 1])
            c1.write(portfolio_id)
            c2.write(name)

            # WICHTIG: stabile ID fürs Löschen + eindeutiger Button-Key
            if c3.button("🗑️", key=f"del_port_{portfolio_id}"):
                if manager.deletePortfolio(portfolio_id):
                    st.rerun()
