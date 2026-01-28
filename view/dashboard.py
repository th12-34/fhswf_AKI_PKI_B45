"""
Seitenname: Dashboard

Autor: Maximilian Pfau / Maxim Sein

Datum: 13.01.2026

Beschreibung:
Dieses Modul bildet das Herzstück der Benutzeroberfläche. Es ermöglicht die Suche
nach Wertpapieren über Yahoo Finance, visualisiert historische Kursdaten inklusive
technischer Indikatoren (MA, RSI, MACD) und integriert die KI-basierte Prognose
sowie Sentiment-Analyse.


Quellen:
- Programmierung
    - https://plotly.com/python/
    - https://yfinance.yahoofinance.com/
    - ChatGPT 5.2
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from prognose_analyse import prognose_analyse
from search import render_ticker_search
from datetime import datetime

# --- Indikatoren ---
# Indikator Gleitender Durchschnitt Optionen
MA_WINDOWS = [20, 50, 200]
MA_COLORS = {
    20: "#cb1e2d",
    50: "#2ca02c",
    200: "#9467bd",
}


def indicator_toogles(windows: list[int]) -> dict[int, bool]:
    """
    Erzeugt Toogle-Buttons in der Tabelle dynamisch.
    """
    cols = st.columns(len(windows))
    return {
        w: cols[i].toggle(f"MA{w}", key=f"show_ma_{w}") for i, w in enumerate(windows)
    }


def add_ma_traces(fig, data, enabled: dict[int, bool]) -> None:
    """
    Fügt Traces für gleitende Durchschnitte dynamisch hinzu.
    """
    close = data["Close"]

    for w, is_on in enabled.items():
        if not is_on:
            continue

        if len(close) < w:
            st.info(f"MA{w}: mindestens {w} Datenpunkte nötig (aktuell {len(close)}).")
            continue

        # Gleitender Durchschnitt berechnen
        ma = close.rolling(window=w, min_periods=w).mean()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=ma,
                mode="lines",
                name=f"MA{w}",
                line=dict(color=MA_COLORS.get(w, None), width=2),
            )
        )


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Berechnet den Relative Strength Index (RSI).
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_bollinger_bands(
    close: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Berechnet Bollinger Bands (SMA ± num_std * Standardabweichung).
    """
    mid = close.rolling(window=window, min_periods=window).mean()
    std = close.rolling(window=window, min_periods=window).std()
    upper = mid + (num_std * std)
    lower = mid - (num_std * std)
    return mid, upper, lower


def compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Berechnet den MACD-Indikator.
    """
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()

    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line

    return macd, signal_line, hist


# -------------------------------


def load_data(symbol, period, interval):
    """
    Lädt die Finanzdaten über Yahoo Finance.
    """
    if not symbol:
        st.session_state["data"] = None
        return

    try:
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

        if data.empty:
            st.error(
                f"Keine Daten gefunden für {symbol} mit Periode {period} und Intervall {interval}."
            )
            st.session_state["data"] = None
            return

        st.session_state["data"] = data
        st.session_state["symbol"] = symbol
        st.session_state["period"] = period
        st.session_state["interval"] = interval
        st.success(f"Daten für {symbol} geladen ({period} / {interval}).")

    except Exception as e:
        st.error(f"Fehler beim Laden der Daten für {symbol}: " + str(e))
        st.session_state["data"] = None


def show_dashboard():
    """
    Rendert das Dashboard-Interface.
    """
    if "selected_symbol" not in st.session_state:
        st.session_state["selected_symbol"] = None
    if "data" not in st.session_state:
        st.session_state["data"] = None

    prog_ana_data = prognose_analyse()
    
    # Nutzung der ausgelagerten Such-Logik
    found_symbol = render_ticker_search(
        key_prefix="dash_search", 
        label="Firmenname, Aktien- oder Krypto-Ticker eingeben"
    )

    if found_symbol:
        if st.session_state.get("selected_symbol") != found_symbol:
            st.session_state["selected_symbol"] = found_symbol
            st.session_state["data"] = None
            st.session_state["prog_result"] = None
            st.session_state["run_prog"] = True
            st.rerun()
    elif found_symbol is None and "dash_search_query_input" in st.session_state and st.session_state["dash_search_query_input"]:
        # Wenn gesucht wurde, aber nichts ausgewählt (oder nichts gefunden), Reset optional
        # Hier behalten wir das alte Symbol bei, solange nichts neues gewählt wird, 
        # oder man könnte st.session_state["selected_symbol"] = None setzen, wenn man strikt sein will.
        pass

    selected_symbol = st.session_state.get("selected_symbol")

    # --- Daten-Optionen ---
    if selected_symbol:
        st.header(f"Daten-Optionen für {selected_symbol}")

        col_period, col_interval = st.columns(2)

        with col_period:
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
            selected_period_label = st.selectbox(
                "Periode auswählen",
                options=list(period_options.keys()),
                index=6,
                key="input_period",
            )
            selected_period_code = period_options[selected_period_label]

        with col_interval:
            interval_options = {
                "1 Stunde (nur 730 Tage)": "1h",
                "1 Tag": "1d",
                "1 Woche": "1wk",
                "1 Monat": "1mo",
            }
            selected_interval_label = st.selectbox(
                "Intervall auswählen",
                options=list(interval_options.keys()),
                index=1,
                key="input_interval",
            )
            selected_interval_code = interval_options[selected_interval_label]

        needs_reload = False

        if st.session_state["data"] is None and selected_symbol:
            needs_reload = True

        elif (
            st.session_state.get("period") != selected_period_code
            or st.session_state.get("interval") != selected_interval_code
        ):
            needs_reload = True

        if needs_reload:
            load_data(selected_symbol, selected_period_code, selected_interval_code)

    # --- Diagramm ---
    if st.session_state["data"] is not None:
        data = st.session_state["data"]
        symbol = st.session_state["symbol"]

        st.divider()

        st.write(f"### Daten für {symbol}")

        latest = data["Close"].iloc[-1]
        prev = data["Close"].iloc[-2] if len(data) > 1 else latest
        diff = latest - prev
        pct = (diff / prev) * 100 if prev != 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Schlusskurs", f"{latest:,.2f} $", f"{diff:,.2f} $")
        c2.metric("Veränderung", f"{pct:.2f} %")
        c3.metric("Datenpunkte", len(data))

        st.markdown("**Indikatoren**")
        enabled = indicator_toogles(MA_WINDOWS)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["Close"],
                mode="lines",
                name="Close",
                #line=dict(color="black", width=2),
            )
        )

        fig.update_layout(
            title=f"{symbol} Schlusskurse", template="streamlit", height=500
        )

        add_ma_traces(fig, data, enabled)
        st.plotly_chart(fig, width="stretch")

        # --- Chart RSI ---
        with st.expander("**RSI**", expanded=True):
            st.markdown(
                    "<h3 style='text-align:center; margin-bottom:0;'>"
                    "Relative Strength Index (RSI)"
                    "</h3>",
                    unsafe_allow_html=True,
            )

            rsi = compute_rsi(data["Close"])

            fig_rsi = go.Figure()
            fig_rsi.add_trace(
                go.Scatter(
                    x=data.index,
                    y=rsi,
                    mode="lines",
                    name="RSI (14)",
                    #line=dict(color="black", width=2),
                )
            )

            # Überkauft (>70) – rot
            fig_rsi.add_hrect(y0=70, y1=100, fillcolor="rgba(255, 80, 80, 0.22)", line_width=0)

            # Überverkauft (<30) – grün
            fig_rsi.add_hrect(y0=0, y1=30, fillcolor="rgba(80, 255, 140, 0.22)", line_width=0)

            # fig_rsi.add_hline(y=70, line_dash="dash")
            # fig_rsi.add_hline(y=30, line_dash="dash")

            fig_rsi.update_layout(
                template="streamlit",
                height=500,
                yaxis_title="RSI",
                yaxis=dict(range=[0, 100]),
            )

            st.plotly_chart(fig_rsi, width="stretch")
            st.caption(
            """Der **Relative Strength Index (RSI)** ist ein *Momentum-Indikator*, der misst, ob ein Asset aktuell **überkauft oder überverkauft** ist.  
            • **RSI > 70** → Überkauft (mögliche Korrektur)  
            • **RSI < 30** → Überverkauft (mögliche Erholung)"""
            )
        # --- Chart MACD ---
        with st.expander("**MACD**", expanded=True):
            st.markdown(
                    "<h3 style='text-align:center; margin-bottom:0;'>"
                    "Moving Average Convergene Divergence (MACD)"
                    "</h3>",
                    unsafe_allow_html=True,
            )

            macd, signal_line, hist = compute_macd(data["Close"])

            fig_macd = go.Figure()
            fig_macd.add_trace(go.Bar(x=data.index, y=hist, name="Histogramm", opacity=0.8))
            fig_macd.add_trace(go.Scatter(x=data.index, y=macd, mode="lines", name="MACD"))
            fig_macd.add_trace(
                go.Scatter(x=data.index, y=signal_line, mode="lines", name="Signal")
            )

            fig_macd.update_layout(template="plotly_dark", height=500, yaxis_title="MACD")

            st.plotly_chart(fig_macd, width="stretch")
            st.caption(
                """Der **Moving Average Convergence Divergence (MACD)** ist ein *Trend- und Momentum-Indikator*, 
                der die Beziehung zweier gleitender Durchschnitte analysiert.  
                • **MACD über Signallinie** → bullisches Signal  
                • **MACD unter Signallinie** → bärisches Signal"""
            )

        # --- Chart Bollinger Bands ---
        with st.expander("**Bollinger Bands**", expanded=True):
            st.markdown(
                "<h3 style='text-align:center; margin-bottom:0;'>"
                "Bollinger Bands"
                "</h3>",
                unsafe_allow_html=True,
            )

            bb_mid, bb_upper, bb_lower = compute_bollinger_bands(data["Close"], window=20, num_std=2.0)

            fig_bb = go.Figure()

            # Close
            fig_bb.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["Close"],
                    mode="lines",
                    name="Close",
                    #line=dict(color="black", width=2),
                )
            )

            # Upper / Lower + filled band
            fig_bb.add_trace(
                go.Scatter(
                    x=data.index,
                    y=bb_upper,
                    mode="lines",
                    name="Upper Band",
                    line=dict(width=1),
                )
            )
            fig_bb.add_trace(
                go.Scatter(
                    x=data.index,
                    y=bb_lower,
                    mode="lines",
                    name="Lower Band",
                    line=dict(width=1),
                    fill="tonexty",
                    fillcolor="rgba(100, 100, 255, 0.12)",
                )
            )

            # Middle (SMA)
            fig_bb.add_trace(
                go.Scatter(
                    x=data.index,
                    y=bb_mid,
                    mode="lines",
                    name="Middle (SMA20)",
                    line=dict(width=1, dash="dot"),
                )
            )

            fig_bb.update_layout(
                template="streamlit",
                height=500,
                yaxis_title="Preis",
            )

            st.plotly_chart(fig_bb, width="stretch")
            st.caption(
                """**Bollinger Bands** sind ein *Volatilitäts-Indikator* um einen gleitenden Durchschnitt (meist SMA20).  
                • Kurs nahe/über **Upper Band** → oft “hoch gelaufen” (nicht automatisch Short)  
                • Kurs nahe/unter **Lower Band** → oft “stark gefallen”  
                • **Bandbreite** steigt → steigende Volatilität"""
            )

        # --- Prognose und Analyse ----
        with st.expander("Kursentwicklungsprognose & Handlungsempfehlung", expanded=True):
            col1, col2 = st.columns(2)

            # Platzhalter (werden sofort gerendert)
            ph_chart = col1.empty()
            ph_text = col2.empty()

            symbol = st.session_state.get("symbol")

            # 1) Wenn noch kein Ergebnis da ist: Platzhalter zeigen
            if st.session_state.get("prog_result") is None:
                ph_chart.info("Prognose wird vorbereitet …")
                ph_text.info("Sentiment wird vorbereitet …")

            # 2) Automatisch starten, sobald Flag gesetzt ist
            if st.session_state.get("run_prog") and symbol:
                with st.spinner("Prognose und Analyse läuft …"):
                    prog_ana_data.update(symbol)

                    progdata, predictions, pred_days = prog_ana_data.get_prediction()
                    empfehlung, news = prog_ana_data.get_sentiment()

                    st.session_state["prog_result"] = (
                        progdata,
                        predictions,
                        pred_days,
                        empfehlung,
                        news,
                    )
                    st.session_state["run_prog"] = False

                st.rerun()  # sorgt dafür, dass danach ohne Spinner sauber gerendert wird

            # 3) Ergebnis rendern, wenn vorhanden
            if st.session_state.get("prog_result") is not None:
                progdata, predictions, pred_days, empfehlung, news = st.session_state[
                    "prog_result"
                ]

                with col1:
                    st.subheader("Kursentwicklungsprognose")
                    figProg = go.Figure()
                    figProg.add_trace(
                        go.Scatter(
                            x=progdata.index,
                            y=progdata[symbol].values,
                            mode="lines",
                            name="Historie",
                        )
                    )
                    figProg.add_trace(
                        go.Scatter(
                            x=pred_days, y=predictions, mode="lines", name="Vorhersage"
                        )
                    )
                    figProg.add_trace(
                        go.Scatter(
                            x=[progdata.index[0], pred_days[-1]],
                            y=[predictions[-1], predictions[-1]],
                            mode="lines",
                            name="Kursziel",
                        )
                    )
                    figProg.update_layout(
                        template="plotly_dark",
                        title="Kursentwicklung und Vorhersage",
                        xaxis_title="Datum",
                        yaxis_title="Kurs",
                    )
                    st.plotly_chart(figProg, width="stretch")

                with col2:
                    st.subheader("News-basierte Handlungsempfehlung")
                    st.markdown(
                        f"<div style='text-align:center;margin-top:30px;font-size:24px;'>{empfehlung}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div style='text-align:center;margin-top:20px;font-size:12px;'>{news}</div>",
                        unsafe_allow_html=True,
                    )

            st.divider()
            if st.button("Neuberechnung der Prognose", use_container_width=True):
                st.session_state["prog_result"] = None
                st.session_state["run_prog"] = True
                st.rerun()
