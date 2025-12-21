import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from gnews import GNews
from google import genai
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def prognose_kurs(stock_symbol):

    # lade Kurse der letzten 90 Tage
    end_date = datetime.today()  # Aktuelles Datum -> Enddatum
    start_date = end_date - timedelta(days=90) # Startdatum
    stock_data = yf.download(stock_symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'),  auto_adjust=True, progress=False)

    # reduziere die Daten auf die Schlusskurse
    data = stock_data['Close']
    #if data.index.freq is None:  # Wenn keine Frequenz vorhanden ist
     #   data = data.asfreq('D')
    #print(data.index) 
    # Approximation mit Arima model
    p_arima = 6 # Anzahl letzter Ausgangswerte
    d_arima = 1 # Anzahl der Differenzbildungen, um statistisch statione Werte zu erhalten
    q_arima = 3 # Anzahl für gleitenden Mittelwert
    model = ARIMA(data, order=(p_arima, d_arima, q_arima))
    model_fit = model.fit()
    # korrektur des Anfangswertes
    #model_fit.fittedvalues.loc[model_fit.fittedvalues.index[0]] = data.iloc[0]
    #model_fit_fitted = model_fit.fittedvalues.copy()  # nötig um fehlermeldungen zu unterdrücken
    #model_fit_fitted.loc[model_fit_fitted.index[0]] = data.iloc[0]

    # vorhersage für die nächsten 14 Tage
    predictions = model_fit.forecast(steps=14)
    # Füge den letzten Wert des historischen Kurses zur Vorhersage hinzu, um die beiden linien im Plot zu verbinden
    predictions = [data.iloc[-1].values[0].tolist()] + list(predictions)
    # Zeitvektor für die Vorsage (x-Achse des ploits)
    pred_days = [data.index[-1] + timedelta(days=i) for i in range(0, 15)]

    return data, predictions, pred_days

def plot_data(data, predictions, pred_days):
        # Plot the actual vs predicted prices
        plt.plot(data.index, data, label='Historie')        
        plt.plot(pred_days, predictions, label='Predicted Prices')             
        plt.legend()
        plt.show()

def news_sentiment(aktienname):
    if not isinstance(aktienname, str):
        assert "wrong type for input: aktienname"

    # initilaisiere news scraper
    gnews = GNews()
    # holen Nachrichten
    news = gnews.get_news(aktienname)
    news_prompt = ""
    for i in range(len(news)):
        news_prompt += f"- {news[i]['description']}\n"

    client = genai.Client(api_key=GEMINI_API_KEY)

    # LLM Abfrage für Handlungsempfehlung
    prompt = "Du bist ein erfahrener Profi am Finanzmarkt. Du hast ein feines Gespür für neue Nachrichten und wie diese sich auf die Kursverläufe von Aktien auswirken. Aus einer Reihe von Nachrichten erstellst du eine Empfehlung. Antworte nur mit Verkaufen, Halten oder Kaufen. Beziehe dich auf folgende News:"
    prompt = f"{prompt} {news_prompt}"    

    response = client.models.generate_content(
    model="gemini-2.5-flash", contents = prompt
    )
    empfehlung = response.text

    # LLM Abfrage um news zu kondensieren
    prompt = "Reduziere folgende News auf die 10 wichtigsten Stichwörter. Wähle diese so, dass sie den massgeblichen Einfluss auf den Aktienkurs der letzten 48 stunden hatten. Gebe nichts anderes, als diese 10 wörter zurück. Benutze keine anderen Quellen als diesen Prompt. News:"
    prompt = f"{prompt} {news_prompt}"    
    response = client.models.generate_content(
    model="gemini-2.5-flash", contents = prompt
    )
    news_reduktion = response.text

    return empfehlung, news_reduktion

#data, predictions, pred_days = prognose_kurs('TSLA')
#plot_data(data, predictions, pred_days)
#rating = news_sentiment('apple')
#print(rating)