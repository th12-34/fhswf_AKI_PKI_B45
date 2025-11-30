import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Konfiguration der Seite (Titel, Layout, Dark Mode initialisieren)
st.set_page_config(page_title="Mein Finanz-Dashboard", layout="wide", initial_sidebar_state="expanded")

def main():
    st.title("📈 Interaktives Finanz-Dashboard")
    st.write("Visualisierung des Schlusskurses (Close Price).")

    # --- SEITENLEISTE (Sidebar) für Eingaben ---
    st.sidebar.header("Einstellungen")
    
    # Wir bieten eine Liste und ein Freitextfeld an
    ticker_liste = ['MSFT', 'AAPL', 'TSLA', 'GOOGL', 'AMZN', 'BTC-USD']
    ticker_select = st.sidebar.selectbox("Aktien-Ticker auswählen", ticker_liste)
    ticker_input = st.sidebar.text_input("Oder Ticker manuell eingeben", value=ticker_select).upper()
    
    # Der tatsächlich genutzte Ticker ist die manuelle Eingabe, falls vorhanden
    ticker = ticker_input if ticker_input else ticker_select

    
    zeitraum_optionen = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max']
    zeitraum = st.sidebar.selectbox("Zeitraum", zeitraum_optionen, index=5) # Standard: '1y'
    
    intervall_optionen = ['1h', '1d', '1wk', '1mo']
    intervall = st.sidebar.selectbox("Intervall", intervall_optionen, index=1) # Standard: '1d'

    if st.sidebar.button("Daten laden"):
        st.toast(f"Lade Daten für {ticker}...", icon="⏳")

    # --- HAUPTBEREICH ---
    if ticker:
        try:
            # Daten laden
            data = yf.download(tickers=ticker, period=zeitraum, interval=intervall, progress=False)

            # Fehler bei yFinance ?
            # Falls yfinance die Spalten als MultiIndex (z.B. Price, Ticker) zurückgibt,
            # reduzieren wir das auf eine einfache Ebene.
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            if data.empty:
                st.error(f"Keine Daten für '{ticker}' gefunden. Bitte prüfe das Kürzel.")
            elif 'Close' not in data.columns:
                 st.error("In den geladenen Daten wurde keine 'Close'-Spalte gefunden.")
            else:
                # --- METRIKEN ---
                # Wir verwenden den 'Close'-Preis
                aktueller_preis = data['Close'].iloc[-1].item()
                letzter_preis = data['Close'].iloc[-2].item() if len(data) > 1 else aktueller_preis
                aenderung = aktueller_preis - letzter_preis
                prozent = (aenderung / letzter_preis) * 100 if letzter_preis != 0 else 0

                col1, col2, col3 = st.columns(3)
                col1.metric("Aktueller Schlusskurs", f"{aktueller_preis:,.2f} $", f"{aenderung:,.2f} $")
                col2.metric("Veränderung (%)", f"{prozent:.2f} %")   #Änderung im letzten Intervall (z.B. 1d - letzer Tag)
                col3.metric("Datensätze (Punkte)", len(data))

                # --- DER GRAPH (Punkte / Scatter) ---
                # Das ist der neue Teil: go.Scatter statt go.Candlestick
                fig = go.Figure(data=[go.Scatter(
                    x=data.index,               # Die Datumsangaben auf der X-Achse
                    y=data['Close'],            # Wir nehmen die 'Close' Spalte
                    mode='lines+markers',       # Linien UND Punkte anzeigen
                    name='Close Price',         # Name in der Legende
                    marker=dict(
                        size=12,                # Größe der Punkte
                        color='cyan',           # Helle Farbe (gut für Dark Mode)
                        line=dict(width=2, color='white'), # Weißer Rand um die Punkte
                        symbol='circle'         # Form des Punktes
                    )
                )])

                # Layout anpassen
                fig.update_layout(
                    title=f'{ticker} - Schlusskurse ({zeitraum})',
                    yaxis_title='Schlusskurs (USD)',
                    xaxis_title='Datum',
                    template='plotly_dark', # Dunkles Design
                    height=600,
                    hovermode="x unified"   # Zeigt Infos an, wenn die Maus über dem Datum ist
                )

                # Y-Achse zwingen, nicht bei 0 anzufangen, sondern beim niedrigsten Kurs
                fig.update_yaxes(autorange=True) 

                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("Zeige Rohdaten Tabelle (zur Kontrolle)"):
                    # Wir zeigen nur die Spalte an, die uns interessiert
                    st.dataframe(data[['Close','High','Low', 'Volume']].tail(10))

        except Exception as e:
            # Ein Trick, um detailliertere Fehlermeldungen zu sehen, falls was schiefgeht
            import traceback
            st.error(f"Ein Fehler ist aufgetreten: {e}")
            with st.expander("Details zum Fehler"):
                 st.code(traceback.format_exc())

if __name__ == "__main__":
    main()