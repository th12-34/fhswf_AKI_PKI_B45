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


def show_view_page():
    
    user = st.session_state.get(Authentication.KEY_USER)
    if not user: 
        st.warning("Bitte logge dich ein.")
        return

    # Manager initialisieren
    if "manager" not in st.session_state:
        st.session_state.manager = PortfolioManager(user["username"])
    
    manager = st.session_state.manager

    # --- 2. Portfolio auswählen ---
    portfolios = manager.getPortfolios()
    if not portfolios:
        st.info("Keine Portfolios gefunden.")
        return

    labels = [f"{p[0]} – {p[1]}" for p in portfolios]
    id_by_label = {label: p[0] for label, p in zip(labels, portfolios)}

    selected_label = st.selectbox("Wähle ein Portfolio", labels)
    selected_portfolio_id = id_by_label[selected_label]
    
    # Manager sagen, welches Portfolio aktiv ist
    manager.selectPortfolioId(selected_portfolio_id)

    # Wert anzeigen
    if manager.currentPortfolio:
        st.metric("Gesamtwert (EUR)", f"{manager.currentPortfolio.get_total_value():.2f} €")

    with st.expander("Neues Asset hinzufügen", expanded=False):

        # --- 3. Suche & Autocomplete ---
        # sonst kein reset der Sucheleiste möglich
        if "reset_nonce" not in st.session_state:
            st.session_state["reset_nonce"] = 0

        query = st.text_input("Suche nach Aktie oder Krypto", key=f"asset_search_query_{st.session_state.reset_nonce}")
        selected_symbol = None

        # Zuerst nach Symbol suchen, dann erst Optionen zum hinzufügen anzeigen, hilft auch für den Form-Reset
        if "show_form" not in st.session_state:
            st.session_state["show_form"] = False
        
        def reset_all():
            for k in [
                "asset_symbol_input",
                "amount_input",
                "price_mode_input",
                "manual_price_input",
                "date_input",
                "asset_choice",
            ]:
                st.session_state.pop(k, None)

            st.session_state.show_form = False
            st.session_state.reset_nonce += 1
            st.rerun()

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

        # --- 4. Formular zum Hinzufügen ---
        if st.session_state["show_form"]:

            with st.form("add_asset_form"): # kein clear_on_submit, da sonst direkt alle Widgets gelöscht werden, auch wenn es eine Fehlermeldung gab
                asset_symbol_val = st.text_input(
                    "Symbol", 
                    key="asset_symbol_input"
                    )
                amount_val = st.number_input(
                    "Menge", 
                    min_value=0.0, 
                    step=0.01, 
                    key="amount_input"
                    )
                date = st.date_input(
                    "Kaufdatum", 
                    value=datetime.date.today(), 
                    key="date_input"
                    )
                preis_modus = st.radio(
                    "Preis", 
                    ["Automatisch", "Manuell"], 
                    key="price_mode_input"
                    )
                manual_price = st.number_input(
                    "Preis pro Einheit", 
                    min_value=0.0,
                    key="manual_price_input",
                    )
                
                submit = st.form_submit_button("Hinzufügen")

                if submit:
                    if not asset_symbol_val or amount_val <= 0:
                        st.error("Bitte Symbol und Menge prüfen.")
                    else:
                        # Preis ermitteln
                        if preis_modus == "Automatisch":
                            price_in_ccy = _fetch_price_for_date(asset_symbol_val, date)
                            ccy = _get_ticker_currency(asset_symbol_val) or "EUR"
                            price_eur = _convert_to_eur(price_in_ccy, ccy, date)                
                        else:
                            price_eur = manual_price

                        if price_eur:
                            # PortfolioAsset Objekt erstellen
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
                            
                            # ÜBER MANAGER HINZUFÜGEN (Wichtig für Refresh!)
                            manager.addAssetToPortfolio(new_asset)
                            st.success(f"{asset_symbol_val} hinzugefügt!")
                            
                            reset_all()
                            st.rerun()
                        else:
                            st.error("Preis konnte nicht ermittelt werden.")
    
    st.divider()

# --- 5. Übersichtstabelle ---
    st.subheader("Aktuelle Assets")

    if manager.currentPortfolio and manager.currentPortfolio.assets:
        header = st.columns([1, 2, 1, 1, 2, 1])
        # Ersetze .bold() durch .markdown() mit **Text**
        header[0].markdown("**Symbol**")
        header[1].markdown("**Name**")
        header[2].markdown("**Typ**")
        header[3].markdown("**Menge**")
        header[4].markdown("**Preis (EUR)**")
        header[5].markdown("**Aktion**")
        st.divider()

        for asset in manager.currentPortfolio.assets:
            cols = st.columns([1, 2, 1, 1, 2, 1])
            cols[0].write(asset.symbol)
            cols[1].write(asset.name or "-")
            cols[2].caption(asset.type)
            cols[3].write(asset.amount)
            cols[4].write(f"{asset.buy_price:.2f} €")
            
            # WICHTIG: asset.id nutzen zum Löschen!
            # Falls asset.id nicht existiert, nutze den Button-Key-Trick von vorhin
            if cols[5].button("🗑️", key=f"del_{asset.portfolio_id}"):
                if manager.deleteAsset(asset.portfolio_id):
                    st.rerun()
    else:
        st.info("Noch keine Assets in diesem Portfolio.")

