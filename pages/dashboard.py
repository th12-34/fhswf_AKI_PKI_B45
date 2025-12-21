import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from prognose_analyse import prognose_analyse
import matplotlib.pyplot as plt


def load_data(symbol, period, interval):
    if not symbol:
        st.session_state["data"] = None
        return

    try:
        data = yf.download(symbol, period=period, interval=interval, progress=False)

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        if data.empty:
            st.error(f"Keine Daten gefunden für {symbol} mit Periode {period} und Intervall {interval}.")
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
    
    prog_ana_data = prognose_analyse()
    query = st.text_input(
        "Gib Aktien- oder Krypto-Ticker oder Namen ein",
        placeholder="z. B. apple, bitcoin, AAPL, BTC-USD",
        key="ticker_query_input"
    )

    if query:
        try:
            if "last_query" not in st.session_state or st.session_state["last_query"] != query:
                result = yf.Search(query, max_results=10)
                st.session_state["search_quotes"] = result.quotes
                st.session_state["last_query"] = query

            quotes = st.session_state["search_quotes"]
            
            if quotes:
                selection_options = []
                symbol_map = {}

                for quote in quotes:
                    symbol = quote["symbol"]
                    name = quote.get("shortname", "N/A")
                    label = f"{symbol} – {name}"
                    selection_options.append(label)
                    symbol_map[label] = symbol

                PLACEHOLDER = "--- Wähle einen Ticker aus der Liste ---"
                all_options = [PLACEHOLDER] + selection_options
                
                selected_label = st.selectbox(
                    "Vorschläge:",
                    options=all_options,
                    index=0,
                    key="autocomplete_selection",
                    label_visibility="collapsed"
                )

                if selected_label != PLACEHOLDER:
                    selected_symbol_code = symbol_map[selected_label]
                    
                    if st.session_state.get("selected_symbol") != selected_symbol_code:
                        st.session_state["selected_symbol"] = selected_symbol_code
                        st.session_state["data"] = None
                        st.rerun()

            else:
                st.write("Keine Vorschläge gefunden.")
                st.session_state["selected_symbol"] = None

        except Exception as e:
            st.write("Fehler bei der Suche:", e)
            st.session_state["selected_symbol"] = None


    selected_symbol = st.session_state.get("selected_symbol")

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
                "1 Jahr": "1y",
                "2 Jahre": "2y",
                "5 Jahre": "5y",
                "Maximal": "max"
            }
            selected_period_label = st.selectbox(
                "Periode auswählen:",
                options=list(period_options.keys()),
                index=5,
                key="input_period"
            )
            selected_period_code = period_options[selected_period_label]


        with col_interval:
            interval_options = {
                "1 Stunde (nur 730 Tage)": "1h",
                "1 Tag": "1d",
                "1 Woche": "1wk",
                "1 Monat": "1mo"
            }
            selected_interval_label = st.selectbox(
                "Intervall auswählen:",
                options=list(interval_options.keys()),
                index=1,
                key="input_interval"
            )
            selected_interval_code = interval_options[selected_interval_label]
            
        
        needs_reload = False
        
        if st.session_state["data"] is None and selected_symbol:
            needs_reload = True
        
        elif st.session_state.get("period") != selected_period_code or \
             st.session_state.get("interval") != selected_interval_code:
            needs_reload = True

        if needs_reload:
            load_data(selected_symbol, selected_period_code, selected_interval_code)


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

        fig = go.Figure(data=[go.Scatter(
            x=data.index,
            y=data["Close"],
            mode="lines",
            name="Close"
        )])
        fig.update_layout(title=f"{symbol} Schlusskurse", template="plotly_dark", height=500)
        st.plotly_chart(fig, width='stretch')

        with st.expander("Rohdaten"):
            st.dataframe(data.tail(20))
        
        # Prognose und Analyse 
        with st.expander("Prognose und Analyse"):
            col1, col2 = st.columns(2)

            if st.button("Prognose und Analyse ausführen"):
                # update data in objekt für prognose und analyse 
                prog_ana_data.update(symbol)

                with st.spinner('Prognose und Analyse läuft...'):                   
                    with col1:
                        st.subheader("Prognose Kursentwicklung")

                        progdata, predictions, pred_days = prog_ana_data.get_prediction()
                    
                        figProg = go.Figure()
                        
                        # historischer Kursverlauf
                        figProg.add_trace(go.Scatter(
                                x = progdata.index,
                                y = progdata[symbol].values,
                                mode="lines",
                                name="Historie"))
    
                        # 7-tagesprognose
                        figProg.add_trace(go.Scatter(
                                x = pred_days,
                                y = predictions,
                                mode="lines",
                                name="Vorhersage"))
                        
                        # 7-tageskursziel
                        figProg.add_trace(go.Scatter(
                                x = [progdata.index[0], pred_days[-1]],
                                y = [predictions[-1], predictions[-1]],
                                mode="lines",
                                name="Kursziel"))
                        
                     
                        figProg.update_layout(
                            title="Kursentwicklung und Vorhersage",
                            xaxis_title="Datum",
                            yaxis_title="Kurs",
                            legend_title="Legende",
                            template="plotly_dark",
                        )
                        st.plotly_chart(figProg, width='stretch')

                    with col2:
                        st.subheader("News-basierte Handlungsempfehlung:")

                        empfehlung, news = prog_ana_data.get_sentiment()
                                           
                        # Darstellung Empfehlung
                        st.markdown(
                            f"""
                            <div style="text-align: center; margin-top: 50px; font-size: 24px;">
                                {empfehlung}
                            </div>
                            """, unsafe_allow_html=True)
                        # Anzeige der wichtigsten News-Stichwörter
                        st.markdown(
                            f"""
                            <div style="text-align: center; margin-top: 50px; font-size: 12px;">
                                {news}
                            </div>
                            """, unsafe_allow_html=True)

                
                


                