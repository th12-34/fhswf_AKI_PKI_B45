"""
Autor: Maximilian Pfau / Maxim Sein

Beschreibung:
Zentrale Komponente für die Ticker-Suche via yfinance.

Quellen:
- Programmierung
    - https://yfinance.yahoofinance.com/
    - https://docs.streamlit.io/
    - Lehrbrief "Python für alle"
    - Gemini
"""

import streamlit as st
import yfinance as yf


def render_ticker_search(key_prefix: str, label: str = "Ticker-Suche"):
    """
    Rendert ein Suchfeld und eine Auswahlbox für Ticker-Vorschläge.
    Nutzt yfinance Search API.

    :param key_prefix: Eindeutiger Prefix für Session-State Keys
    :param label: Label für das Text-Input Feld
    :return: Der ausgewählte Ticker-Symbol-String oder None
    """
    query = st.text_input(
        label,
        placeholder="z. B. apple, bitcoin, AAPL, BTC-USD",
        key=f"{key_prefix}_query_input",
    )

    if not query:
        return None

    try:
        # Keys für Caching
        quotes_key = f"{key_prefix}_quotes"
        last_query_key = f"{key_prefix}_last_query"

        # Nur suchen, wenn sich die Query geändert hat
        if (
            last_query_key not in st.session_state
            or st.session_state[last_query_key] != query
        ):
            result = yf.Search(query, max_results=10)
            st.session_state[quotes_key] = result.quotes
            st.session_state[last_query_key] = query

        quotes = st.session_state.get(quotes_key)

        if quotes:
            selection_options = []
            symbol_map = {}

            for quote in quotes:
                symbol = quote["symbol"]
                name = quote.get("shortname", "N/A")
                label_opt = f"{symbol} – {name}"
                selection_options.append(label_opt)
                symbol_map[label_opt] = symbol

            PLACEHOLDER = "--- Wähle einen Ticker aus der Liste ---"
            all_options = [PLACEHOLDER] + selection_options

            selected_label = st.selectbox(
                "Vorschläge:",
                options=all_options,
                index=0,
                key=f"{key_prefix}_autocomplete_selection",
                label_visibility="collapsed",
            )

            if selected_label != PLACEHOLDER:
                return symbol_map[selected_label]
        else:
            st.info("Keine Vorschläge gefunden.")
            return None

    except Exception as e:
        st.error(f"Fehler bei der Suche: {e}")
        return None

    return None
