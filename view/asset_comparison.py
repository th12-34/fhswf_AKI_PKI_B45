"""
Seitenname: Asset-Vergleich

Autor: Gregor Schumacher

Beschreibung:
Vergleicht zwei Assets, die über die bestehende Suche (render_ticker_search) ausgewählt werden.
Zeigt Preisvergleich (Close), normalisierte Performance (Start=100) sowie Basis-Metriken
(letzter Close, Veränderung über Zeitraum, Korrelation der Returns).

Hinweis:
- Nutzt eigene Session-State Keys (cmp_...), um keine Kollision mit dem Dashboard zu erzeugen.
- Wiederverwendet render_ticker_search exakt wie im Dashboard, aber zweimal mit unterschiedlichem key_prefix.

Quellen:
- Vorwissen
- https://plotly.com/python/
- https://yfinance.yahoofinance.com/
- https://pandas.pydata.org/pandas-docs/stable/user_guide/10min.html
- ChatGPT 5.2
"""


import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from search import render_ticker_search


# Helperfunktionen

def _download_data(symbol: str, period: str, interval: str) -> pd.DataFrame:
    """Lädt Daten über yfinance."""
    if not symbol:
        return pd.DataFrame()

    if period == "ytd":
        now = datetime.now()
        start = datetime(now.year, 1, 1)
        data = yf.download(
            symbol, start=start, end=now, interval=interval, progress=False
        )
    else:
        data = yf.download(symbol, period=period, interval=interval, progress=False)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    return data


def _calc_change_over_period(close: pd.Series) -> tuple[float, float]:
    """Berechnet absolute und prozentuale Veränderung über den gesamten Zeitraum."""
    if close is None or close.empty:
        return 0.0, 0.0

    first = float(close.iloc[0])
    last = float(close.iloc[-1])

    abs_change = last - first
    pct_change = (abs_change / first * 100.0) if first != 0 else 0.0
    return abs_change, pct_change


def _ensure_state_defaults() -> None:
    """Initialisiert Session-State Defaults."""
    defaults = {
        "cmp_symbol_a": None,
        "cmp_symbol_b": None,
        "cmp_data_a": None,
        "cmp_data_b": None,
        "cmp_period": None,
        "cmp_interval": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# Asset-Vergleich Page

def show_asset_comparison_page():
    _ensure_state_defaults()

    st.caption("In dieser Ansicht können Sie zwei beliebige Assets miteinander vergleichen. ")

    # Suche
    c1, c2 = st.columns(2)

    with c1:
        found_a = render_ticker_search(
            key_prefix="cmp_a",
            label="Asset A - Firmenname, Aktie oder Krypto-Ticker"
        )

    with c2:
        found_b = render_ticker_search(
            key_prefix="cmp_b",
            label="Asset B - Firmenname, Aktie oder Krypto-Ticker"
        )

    # Auswahl stabil in Session speichern
    if found_a:
        if st.session_state.get("cmp_symbol_a") != found_a:
            st.session_state["cmp_symbol_a"] = found_a
            st.session_state["cmp_data_a"] = None

    if found_b:
        if st.session_state.get("cmp_symbol_b") != found_b:
            st.session_state["cmp_symbol_b"] = found_b
            st.session_state["cmp_data_b"] = None

    symbol_a = st.session_state.get("cmp_symbol_a")
    symbol_b = st.session_state.get("cmp_symbol_b")

    # Flag: identisches Asset ausgewählt?
    same_asset = bool(symbol_a and symbol_b and symbol_a == symbol_b)

    st.divider()

    # Daten-Optionen (period/interval)
    period_options = {
        "1 Tag (Intraday)": "1d",
        "5 Tage": "5d",
        "1 Monat": "1mo",
        "3 Monate": "3mo",
        "6 Monate": "6mo",
        "YTD": "ytd",
        "1 Jahr": "1y",
        "2 Jahre": "2y",
        "5 Jahre": "5y",
        "Maximal": "max",
    }
    interval_options = {
        "1 Stunde (nur 730 Tage)": "1h",
        "1 Tag": "1d",
        "1 Woche": "1wk",
        "1 Monat": "1mo",
    }

    o1, o2 = st.columns(2)

    with o1:
        selected_period_label = st.selectbox(
            "Periode auswählen",
            options=list(period_options.keys()),
            index=6,
            key="cmp_input_period",
        )
    with o2:
        selected_interval_label = st.selectbox(
            "Intervall auswählen",
            options=list(interval_options.keys()),
            index=1,
            key="cmp_input_interval",
        )

    period = period_options[selected_period_label]
    interval = interval_options[selected_interval_label]

    # Wenn sich die Optionen ändern: Daten neu laden
    if st.session_state["cmp_period"] is None:
        st.session_state["cmp_period"] = period
    if st.session_state["cmp_interval"] is None:
        st.session_state["cmp_interval"] = interval

    if st.session_state["cmp_period"] != period or st.session_state["cmp_interval"] != interval:
        st.session_state["cmp_period"] = period
        st.session_state["cmp_interval"] = interval
        st.session_state["cmp_data_a"] = None
        st.session_state["cmp_data_b"] = None

    # Daten laden 
    if symbol_a and st.session_state.get("cmp_data_a") is None:
        with st.spinner(f"Lade Daten für {symbol_a} ({period}/{interval}) …"):
            data_a = _download_data(symbol_a, period, interval)

        if data_a.empty:
            st.error(f"Keine Daten gefunden für {symbol_a} ({period}/{interval}).")
            st.session_state["cmp_data_a"] = pd.DataFrame()
        else:
            st.session_state["cmp_data_a"] = data_a

    if symbol_b and st.session_state.get("cmp_data_b") is None:
        with st.spinner(f"Lade Daten für {symbol_b} ({period}/{interval}) …"):
            data_b = _download_data(symbol_b, period, interval)

        if data_b.empty:
            st.error(f"Keine Daten gefunden für {symbol_b} ({period}/{interval}).")
            st.session_state["cmp_data_b"] = pd.DataFrame()
        else:
            st.session_state["cmp_data_b"] = data_b

    data_a = st.session_state.get("cmp_data_a")
    data_b = st.session_state.get("cmp_data_b")

    # Vorsichtsmaßnahmen 
    if not symbol_a or not symbol_b:
        st.info("Bitte wähle **zwei Assets** aus, um sie zu vergleichen.")
        return

    if data_a is None or data_b is None or data_a.empty or data_b.empty:
        st.warning("Für mindestens eines der Assets sind keine Daten verfügbar.")
        return

    # Interne Labels (garantiert eindeutig)
    label_a = f"{symbol_a} (A)"
    label_b = f"{symbol_b} (B)"

    # Daten ausrichten / zusammenführen
    close_a = data_a["Close"].dropna().rename(label_a)
    close_b = data_b["Close"].dropna().rename(label_b)

    df = pd.concat([close_a, close_b], axis=1).dropna()

    if df.empty or len(df) < 2:
        st.warning("Zu wenige überlappende Datenpunkte für einen Vergleich.")
        return

    # Metriken
    latest_a = float(df[label_a].iloc[-1])
    latest_b = float(df[label_b].iloc[-1])

    abs_a, pct_a = _calc_change_over_period(df[label_a])
    abs_b, pct_b = _calc_change_over_period(df[label_b])

    returns = df.pct_change().dropna()
    corr = float(returns[label_a].corr(returns[label_b])) if not returns.empty else float("nan")

    c1, c2, c3 = st.columns(3)
    c1.metric(f"{label_a} Schlusskurs", f"{latest_a:,.2f} $", f"{pct_a:.2f} %")
    c2.metric(f"{label_b} Schlusskurs", f"{latest_b:,.2f} $", f"{pct_b:.2f} %")
    c3.metric("Korrelation (Returns)", f"{corr:.2f}")
    
    st.write("")
    st.text(
        f"Zeitraum-Änderung: {label_a}: {abs_a:,.2f} $ | {label_b}: {abs_b:,.2f} $"
    )

    # Besseren Performer bei unterschiedlichen Assets identifizieren
    if not same_asset:
        # Toleranz, um “quasi gleich” sauber als unentschieden zu behandeln
        tol = 1e-6
        delta = pct_a - pct_b

        if abs(delta) <= tol:
            st.info("📌 Beide Assets haben im gewählten Zeitraum **nahezu gleich** performt.")
        elif delta > 0:
            st.success(f"🏆 **{symbol_a}** hat im gewählten Zeitraum besser performt als **{symbol_b}** "
                       f"({pct_a:.2f}% vs. {pct_b:.2f}%).")
        else:
            st.success(f"🏆 **{symbol_b}** hat im gewählten Zeitraum besser performt als **{symbol_a}** "
                       f"({pct_b:.2f}% vs. {pct_a:.2f}%).")

    st.divider()

    # Chart 1: Preisvergleich
    with st.expander("**Preisvergleich**", expanded=True):
        st.markdown(
            "<h3 style='text-align:center; margin-bottom:0;'>"
            "Preisvergleich (Close)"
            "</h3>",
            unsafe_allow_html=True,
        )
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(x=df.index, y=df[label_a], mode="lines", name=label_a))
        fig_price.add_trace(go.Scatter(x=df.index, y=df[label_b], mode="lines", name=label_b))
        fig_price.update_layout(template="streamlit", height=500, yaxis_title="Preis")
        st.plotly_chart(fig_price, width="stretch")
        st.caption(
            """Vergleich der **Schlusskurse (Close)** beider Assets im gewählten Zeitraum.  
            • Zeigt den **absoluten Preisverlauf** (nicht normalisiert)  
            • Gut zur Einschätzung von **Trend, Volatilität und Drawdowns**  
            • Preisniveaus sind **nicht direkt vergleichbar** – dafür den Performance-Chart nutzen"""
        )

    # Chart 2: Normalisierte Performance
    with st.expander("**Performancevergleich**", expanded=True):
        st.markdown(
            "<h3 style='text-align:center; margin-bottom:0;'>"
            "Performancevergleich (Start = 100)"
            "</h3>",
            unsafe_allow_html=True,
        )
        norm = df / df.iloc[0] * 100.0

        fig_norm = go.Figure()
        fig_norm.add_trace(go.Scatter(x=norm.index, y=norm[label_a], mode="lines", name=label_a))
        fig_norm.add_trace(go.Scatter(x=norm.index, y=norm[label_b], mode="lines", name=label_b))
        fig_norm.update_layout(template="streamlit", height=500, yaxis_title="Index (Start=100)")
        st.plotly_chart(fig_norm, width="stretch")
        st.caption(
            """Vergleich der **relativen Performance** beider Assets mit identischem Startwert (**Index = 100**).  
            • Zeigt, **welches Asset besser performt**, unabhängig vom Preisniveau  
            • Abstände entsprechen **prozentualen Rendite-Unterschieden**  
            • Ideal für **Outperformance-, Trend- und Timing-Analysen**"""
        )

    st.divider()

    with st.expander("Daten anzeigen"):
        st.dataframe(df.tail(50), width="stretch")

    if st.button("Daten neu laden", use_container_width=True):
        st.session_state["cmp_data_a"] = None
        st.session_state["cmp_data_b"] = None
        st.rerun()
