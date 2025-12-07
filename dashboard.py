import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

def show_dashboard():
    st.title("📈 Interaktives Finanz-Dashboard")

    # Sidebar
    st.sidebar.header("Einstellungen")

    ticker_liste = ['MSFT', 'AAPL', 'TSLA', 'GOOGL', 'AMZN', 'BTC-USD']
    ticker_select = st.sidebar.selectbox("Aktie wählen", ticker_liste)
    ticker_input = st.sidebar.text_input("Oder manuell eingeben", value=ticker_select).upper()

    ticker = ticker_input if ticker_input else ticker_select

    zeitraum_optionen = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']
    zeitraum = st.sidebar.selectbox("Zeitraum", zeitraum_optionen, index=5)

    intervall_optionen = ['1h', '1d', '1wk', '1mo']
    intervall = st.sidebar.selectbox("Intervall", intervall_optionen, index=1)

    if st.sidebar.button("Daten laden"):
        st.toast(f"Lade Daten für {ticker}...", icon="⏳")

    try:
        data = yf.download(
            tickers=ticker, period=zeitraum, interval=intervall, progress=False
        )

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if data.empty:
            st.error("Keine Daten gefunden.")
            return

        aktueller_preis = data["Close"].iloc[-1]
        letzter_preis = data["Close"].iloc[-2] if len(data) > 1 else aktueller_preis
        aenderung = aktueller_preis - letzter_preis
        prozent = (aenderung / letzter_preis) * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("Schlusskurs", f"{aktueller_preis:,.2f} $", f"{aenderung:.2f} $")
        c2.metric("Veränderung", f"{prozent:.2f} %")
        c3.metric("Datenpunkte", len(data))

        fig = go.Figure(data=[go.Scatter(
            x=data.index,
            y=data["Close"],
            mode="lines+markers",
            marker=dict(size=10),
        )])

        fig.update_layout(
            title=f"{ticker} Schlusskurse",
            template="plotly_dark",
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Rohdaten anzeigen"):
            st.dataframe(data.tail(20))

    except Exception as e:
        st.error(str(e))