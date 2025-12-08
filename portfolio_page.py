import datetime
import streamlit as st
import yfinance as yf
import pandas as pd

from useradministration import UserAdministration
from authentication import Authentication


ua = UserAdministration()
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


def show_add_assets_page():
    st.title("Portfolio & Assets verwalten")

    user = auth.get_logged_in_user()
    if not user:
        st.warning("Bitte logge dich zuerst ein, um dein Portfolio zu verwalten.")
        return

    username = user["username"]

    portfolios = ua.get_portfolios_for_user(username)
    if not portfolios:
        st.info("Du hast noch kein Portfolio. Es wird ein Standard-Portfolio automatisch beim Registrieren angelegt.")
        return

    labels = [f"{p['id']} – {p['portfolio_name']}" for p in portfolios]
    id_by_label = {label: p["id"] for label, p in zip(labels, portfolios)}

    selected_label = st.selectbox("Wähle ein Portfolio", labels)
    selected_portfolio_id = id_by_label[selected_label]

    st.subheader("Neues Asset hinzufügen")

    # ---------- Autocomplete für Symbol ----------
    query = st.text_input(
        "Suche nach Aktie oder Krypto (Name oder Ticker)",
        key="asset_search_query",
        placeholder="z. B. apple, bitcoin, AAPL, BTC-USD",
    )

    selected_symbol = None
    detected_name = None
    detected_type = None

    if query:
        try:
            if (
                "asset_last_query" not in st.session_state
                or st.session_state["asset_last_query"] != query
            ):
                result = yf.Search(query, max_results=10)
                st.session_state["asset_search_quotes"] = result.quotes
                st.session_state["asset_last_query"] = query

            quotes = st.session_state.get("asset_search_quotes", [])

            if quotes:
                options = []
                quote_by_label = {}
                for q in quotes:
                    symbol = q.get("symbol")
                    if not symbol:
                        continue
                    name = q.get("shortname") or q.get("longname") or "N/A"
                    label = f"{symbol} – {name}"
                    options.append(label)
                    quote_by_label[label] = q

                placeholder = "--- Wähle einen Treffer aus ---"
                all_options = [placeholder] + options

                selected_quote_label = st.selectbox(
                    "Vorschläge",
                    options=all_options,
                    index=0,
                    key="asset_autocomplete_selection",
                )

                if selected_quote_label != placeholder:
                    q = quote_by_label[selected_quote_label]
                    selected_symbol = q.get("symbol")
                    detected_name = q.get("shortname") or q.get("longname")
                    detected_type = _infer_asset_type(selected_symbol, q.get("quoteType"))

                    # >>> WICHTIG: Symbol direkt ins Textfeld-State schreiben
                    st.session_state["asset_symbol_input"] = selected_symbol

        except Exception as e:
            st.error(f"Fehler bei der Suche: {e}")

    # ---------- Formular ----------
    # clear_on_submit=False, damit Eingaben NICHT verloren gehen
    with st.form("add_asset_form", clear_on_submit=False):
        asset_symbol = st.text_input(
            "Ticker / Symbol",
            key="asset_symbol_input",
            placeholder="z. B. AAPL, BTC-USD",
        )

        default_name = detected_name or st.session_state.get("asset_name_input", "")
        asset_name = st.text_input(
            "Name (optional – wird sonst automatisch versucht)",
            value=default_name,
            key="asset_name_input",
        )

        inferred_type_display = detected_type or (
            _infer_asset_type(asset_symbol) if asset_symbol else None
        )

        if inferred_type_display:
            st.markdown(f"**Erkannter Typ:** `{inferred_type_display}`")
        else:
            st.markdown("**Erkannter Typ:** _unbekannt_ (wird als 'stock' behandelt)")

        amount = st.number_input(
            "Menge",
            min_value=0.0,
            step=0.01,
            key="asset_amount_input",
        )

        preis_modus = st.radio(
            "Kaufpreis bestimmen",
            ["Automatisch (Schlusskurs am Datum)", "Manuell eingeben"],
            key="asset_price_mode",
        )

        manual_price = None
        if preis_modus == "Manuell eingeben":
            manual_price = st.number_input(
                "Kaufpreis pro Einheit",
                min_value=0.0,
                step=0.01,
                key="asset_manual_price_input",
            )

        date = st.date_input(
            "Kaufdatum",
            value=st.session_state.get("asset_date_input", datetime.date.today()),
            key="asset_date_input",
        )
        time = st.time_input(
            "Kaufzeit",
            value=st.session_state.get(
                "asset_time_input",
                datetime.datetime.now().time()
            ),
            key="asset_time_input",
        )

        submit = st.form_submit_button("Ins Portfolio übernehmen")

        if submit:
            asset_symbol_val = st.session_state.get("asset_symbol_input", "").strip()
            amount_val = st.session_state.get("asset_amount_input", 0.0)

            if not asset_symbol_val:
                st.error("Bitte gib ein Symbol ein (oder wähle eines aus den Vorschlägen).")
                return
            if amount_val <= 0:
                st.error("Menge muss größer als 0 sein.")
                return

            bought_at_dt = datetime.datetime.combine(date, time)

            # Asset-Typ bestimmen
            final_asset_type = inferred_type_display or _infer_asset_type(asset_symbol_val)
            if final_asset_type not in ("stock", "crypto"):
                final_asset_type = "stock"

            # 1) Preis in der Original-Währung (laut Börse) bestimmen
            if preis_modus == "Automatisch (Schlusskurs am Datum)":
                price_in_ccy = _fetch_price_for_date(asset_symbol_val, date)
                if price_in_ccy is None:
                    st.error(
                        "Automatische Preisermittlung nicht möglich – bitte manuell eingeben."
                    )
                    return
            else:
                manual_price_val = st.session_state.get("asset_manual_price_input", 0.0)
                if manual_price_val <= 0:
                    st.error("Bitte gib einen Kaufpreis > 0 ein.")
                    return
                price_in_ccy = float(manual_price_val)

            # 2) Handelswährung automatisch über den Ticker bestimmen
            ticker_ccy = _get_ticker_currency(asset_symbol_val)  # z.B. 'USD', 'EUR', ...
            if not ticker_ccy:
                st.error(
                    "Konnte die Handelswährung nicht automatisch bestimmen. "
                    "Bitte überprüfe das Symbol."
                )
                return

            # 3) In EUR umrechnen
            price_in_eur = _convert_to_eur(price_in_ccy, ticker_ccy, date)
            if price_in_eur is None:
                st.error(
                    f"Kein Wechselkurs {ticker_ccy}->EUR gefunden. "
                    "Bitte wähle ggf. ein anderes Symbol oder speichere mit EUR-Preis."
                )
                return

            # 4) Name ggf. automatisch nachziehen
            asset_name_val = st.session_state.get("asset_name_input", "").strip()
            asset_name_to_store = asset_name_val if asset_name_val else None
            if asset_name_to_store is None:
                auto_name = _fetch_yf_name(asset_symbol_val)
                if auto_name:
                    asset_name_to_store = auto_name

            bought_at_str = bought_at_dt.strftime("%Y-%m-%d %H:%M:%S")

            asset_id = ua.add_asset(
                portfolio_id=selected_portfolio_id,
                asset_type=final_asset_type,
                asset_symbol=asset_symbol_val,
                asset_name=asset_name_to_store,
                amount=amount_val,
                buy_price=price_in_eur,   # <<< IMMER EUR
                bought_at=bought_at_str,
                # falls du eine currency-Spalte hast, kannst du hier "EUR" oder ticker_ccy mitgeben
            )

            if asset_id is not None:
                st.success(
                    f"Asset wurde hinzugefügt (ID: {asset_id}) – "
                    f"Kurs in Börsenwährung: {price_in_ccy:.2f} {ticker_ccy}, "
                    f"gespeichert: {price_in_eur:.2f} €"
                )
            else:
                st.error("Fehler beim Hinzufügen des Assets.")


    # ---------- Übersicht + Delete ----------
    st.subheader("Assets im ausgewählten Portfolio")

    assets = ua.get_assets_for_portfolio(selected_portfolio_id)
    if not assets:
        st.info("Dieses Portfolio enthält noch keine Assets.")
        return

    st.markdown("#### Übersicht")

    # Kopfzeile
    header_cols = st.columns([1, 2, 2, 2, 2, 1])
    header_cols[0].markdown("**ID**")
    header_cols[1].markdown("**Symbol / Name**")
    header_cols[2].markdown("**Typ**")
    header_cols[3].markdown("**Menge**")
    header_cols[4].markdown("**Kaufpreis & Datum**")
    header_cols[5].markdown("**Aktion**")

    # Tabellenzeilen
    for asset in assets:
        cols = st.columns([1, 2, 2, 2, 2, 1])

        with cols[0]:
            st.write(asset["id"])

        with cols[1]:
            name = asset.get("asset_name") or ""
            st.write(f"{asset['asset_symbol']}")
            if name:
                st.caption(name)

        with cols[2]:
            st.write(asset["asset_type"])

        with cols[3]:
            st.write(asset["amount"])

        with cols[4]:
            st.write(f"Preis: {asset['buy_price']:.2f}")

        with cols[5]:
            if st.button("🗑️", key=f"delete_asset_{asset['id']}"):
                ok = ua.delete_asset(asset["id"])
                if ok:
                    st.success(f"Asset mit ID {asset['id']} gelöscht.")
                    st.rerun()
                else:
                    st.error("Löschen fehlgeschlagen.")

