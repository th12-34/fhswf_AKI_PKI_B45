import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from gnews import GNews
from google import genai
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class prognose_analyse:
     
    def __init__(self):
        self.Firmenname = ''

        pred_dict = {}
        pred_dict['hist_data'] = None
        pred_dict['pred'] = {}
        pred_dict['pred']['Tage'] = []
        pred_dict['pred']['Werte'] = []
        self.pred_dict = pred_dict

        sent_dict = {}
        sent_dict['news'] = ''
        sent_dict['news_red'] = ''
        sent_dict['empfehlung'] = ''
        self.sent_dict = sent_dict
        

    def ticker2Firma(self, tickername):
        # Tickername -> Firmenname
        FirmenName = yf.Ticker(tickername).info.get('longName')
        self.FirmenName = FirmenName

        return FirmenName


    def prognose_kurs(self, tickername):

        # lade Kurse der letzten 90 Tage
        end_date = datetime.today()  # Aktuelles Datum -> Enddatum
        start_date = end_date - timedelta(days=90) # Startdatum
        stock_data = yf.download(tickername, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'),  auto_adjust=True, progress=False)

        # reduziere die Daten auf die Schlusskurse
        data = stock_data['Close']

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
        # Zeitvektor für die Vorsage (x-Achse des plots)
        pred_days = [data.index[-1] + timedelta(days=i) for i in range(0, 15)]

        self.pred_dict['hist_data'] = data
        self.pred_dict['pred']['Tage'] = predictions
        self.pred_dict['pred']['Werte'] = pred_days
   

    def news_sentiment(self, tickername):

        FirmenName = self.ticker2Firma(tickername)

        if not isinstance(FirmenName, str):
            assert "wrong type for input: FirmenName"

        # initialisiere news scraper
        gnews = GNews()
        # hole Nachrichten
        news = gnews.get_news(FirmenName)
        # reduziere news auf die reinen Meldungen (Key: 'description')
        news_prompt = ""
        for i in range(len(news)):
            news_prompt += f"- {news[i]['description']}\n"

        # initialisiere LLM
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Prompt-Erstellung
        prompt = "Du bist ein erfahrener Profi am Finanzmarkt. Du hast ein feines Gespür für neue Nachrichten und wie diese sich auf die Kursverläufe von Aktien auswirken. Aus einer Reihe von Nachrichten erstellst du eine Empfehlung. Antworte nur mit Verkaufen, Halten oder Kaufen. Beziehe dich auf folgende News:"
        prompt = f"{prompt} {news_prompt}"

        try:
            # LLM Abfrage für Handlungsempfehlung
            response = client.models.generate_content(
            model="gemini-2.5-flash", contents = prompt
            )
            if response.status_code == 200:
                empfehlung = response.text
        except:
            empfehlung = 'Google Gemini derzeit nicht erreichbar'

        # Ergänzung um Pfeilsymbol
        if empfehlung == 'Verkaufen':
            arrow = '⬇️'
        elif empfehlung == 'Halten':
            arrow = '➡️'
        elif empfehlung == 'Kaufen':
            arrow = '⬆️'
        else:
            arrow = ' '            

        empfehlung = empfehlung + ' ' + arrow

        # prompt um news zu kondensieren
        prompt = "Reduziere folgende News auf die 10 wichtigsten Stichwörter. Wähle diese so, dass sie den massgeblichen Einfluss auf den Aktienkurs der letzten 48 stunden hatten. Gebe nichts anderes, als diese 10 wörter zurück. Benutze keine anderen Quellen als diesen Prompt. News:"
        prompt = f"{prompt} {news_prompt}"

        try:
            # LLM Abfrage um news zu kondensieren
            response = client.models.generate_content(
            model="gemini-2.5-flash", contents = prompt
            )
            if response.status_code == 200:
                news_reduktion = response.text
        except:
            news_reduktion = 'Google Gemini derzeit nicht erreichbar'
        

        # update class attributes
        self.sent_dict['news'] = news
        self.sent_dict['news_red'] = news_reduktion
        self.sent_dict['empfehlung'] = empfehlung

    def update(self, tickername):
        self.news_sentiment(tickername)
        self.prognose_kurs(tickername)


    def get_sentiment(self):
        empfehlung = self.sent_dict['empfehlung']
        news_reduktion = self.sent_dict['news_red']

        return empfehlung, news_reduktion

    def get_prediction(self):

        pred_data = self.pred_dict['hist_data']
        predictions = self.pred_dict['pred']['Tage']
        pred_days = self.pred_dict['pred']['Werte']

        return pred_data, predictions, pred_days