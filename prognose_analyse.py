"""
Programmname: prognose_analyse

Autor: Thorben Herfeld

Datum: 12.01.2026

Beschreibung:
Diese Klasse stellt Methoden bereit, um basierend auf yfinance Daten
Empfehlungen für den Kauf oder Verkauf einer Aktie zu ermitteln.
"""

import yfinance as yf
from statsmodels.tsa.arima.model import ARIMA
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from gnews import GNews
from google import genai
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class prognose_analyse:
    """
    Diese Klasse stellt Methoden bereit, um basierend auf yfinance Daten
    Empfehlungen für den Kauf oder Verkauf einer Aktie zu ermitteln.
    """
     
    def __init__(self):
        """
        Initialisiert eine Intsanz der Klasse 'prognose_analyse' mit leeren Werten der Attribute.

        :param -
        :return: -
        """
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
        """
        Übersetze den yFinance-Tickernamen in den offiziellen Firmennamen (e.g. APPL -> Apple)

        :param - tickername: offzielles Kuerzel wie von yFinance verwendet
        :return - FirmenName: Name der Aktienfirma, wie von yFinance geführt
        """
        # Tickername -> Firmenname
        FirmenName = yf.Ticker(tickername).info.get('longName')
        self.FirmenName = FirmenName

        return FirmenName


    def prognose_kurs(self, tickername):
        """
        Lade über den Tickernamen den Kursverlauf der letzten 90 Tage, approximiere
        diesen Verlauf mittels eines ARIMA-Modells und berechne einen möglichen Verlauf
        der kommenden 14 Tage.

        :param - tickername: offzielles Kuerzel wie von yFinance verwendet
        :return - keine (Ergebnisse werden auf Attribute geschrieben)
        """

        # lade Kurse der letzten 90 Tage
        end_date = datetime.today()  # Aktuelles Datum -> Enddatum
        start_date = end_date - timedelta(days=90) # Startdatum
        kursverlauf = yf.download(tickername, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'),  auto_adjust=True, progress=False)

        # reduziere die Daten auf die Schlusskurse des Tages
        data = kursverlauf['Close']

        # Approximation mit Arima model
        p_arima = 6 # Anzahl letzter Ausgangswerte
        d_arima = 1 # Anzahl der Differenzbildungen, um statistisch stationäre Werte zu erhalten
        q_arima = 3 # Anzahl für gleitenden Mittelwert
        model = ARIMA(data, order=(p_arima, d_arima, q_arima))
        model_fit = model.fit()

        # vorhersage für die nächsten 14 Tage
        predictions = model_fit.forecast(steps=14)
        # Füge den letzten Wert des historischen Kurses zur Vorhersage hinzu, um die beiden linien im Plot zu verbinden
        predictions = [data.iloc[-1].values[0].tolist()] + list(predictions)
        # Zeitvektor für die Vorsage (x-Achse des plots)
        pred_days = [data.index[-1] + timedelta(days=i) for i in range(0, 15)]

        # Schreibe Werte auf Attribute
        self.pred_dict['hist_data'] = data
        self.pred_dict['pred']['Tage'] = predictions
        self.pred_dict['pred']['Werte'] = pred_days
   

    def news_sentiment(self, tickername):
        """
        Lade per Google-Suche die neuesten Nachrichten zu gewählten Aktienfirma und leite daraus 
        eine Kaufempfehlung ab

        :param - tickername: offzielles Kuerzel wievon yFinance verwendet
        :return - keine (Ergebnisse werden auf Attribute geschrieben)
        """

        # tickername -> Firmenname
        FirmenName = self.ticker2Firma(tickername)

        try:
            # initialisiere news scraper
            gnews = GNews()
            # hole Nachrichten
            news = gnews.get_news(FirmenName)
            # reduziere news auf die reinen Meldungen (Key: 'description')
            news_prompt = ""
            for i in range(len(news)):
                news_prompt += f"- {news[i]['description']}\n"

        except:
            err_msg = 'Git news ist nicht erreichbar'
            # update class attributes
            self.sent_dict['news'] = err_msg
            self.sent_dict['news_red'] = err_msg
            self.sent_dict['empfehlung'] = err_msg

            return        

        # initialisiere LLM
        if GEMINI_API_KEY is None or GEMINI_API_KEY == "":
            err_msg = 'Pruefe GEMINI API KEY'
            self.sent_dict['news_red'] = err_msg
            self.sent_dict['empfehlung'] = err_msg
            return
    
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Prompt-Erstellung
        prompt = "Du bist ein erfahrener Profi am Finanzmarkt. Du hast ein feines Gespür für neue Nachrichten und wie diese sich auf die Kursverläufe von Aktien auswirken. Aus einer Reihe von Nachrichten erstellst du eine Empfehlung. Antworte nur mit Verkaufen, Halten oder Kaufen. Beziehe dich auf folgende News:"
        prompt = f"{prompt} {news_prompt}"

        try:
            # LLM Abfrage für Handlungsempfehlung
            response = client.models.generate_content(
            model="gemini-2.5-flash", contents = prompt
            )
            empfehlung = getattr(response, "text", None)
            if not empfehlung:
                empfehlung = 'Google Gemini derzeit nicht erreichbar'

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
        prompt = "Reduziere folgende News auf die 10 wichtigsten Stichwörter. Wähle diese so, dass sie den massgeblichen Einfluss auf den Aktienkurs der letzten 48 stunden hatten. Gebe nichts anderes, als diese 10 wörter zurück. Trenne diese durch ein Komma. Benutze keine anderen Quellen als diesen Prompt. News:"
        prompt = f"{prompt} {news_prompt}"

        try:
            # LLM Abfrage um news zu kondensieren
            response = client.models.generate_content(
            model="gemini-2.5-flash", contents = prompt
            )
            news_reduktion = getattr(response, "text", None)
            if not news_reduktion:
                news_reduktion = 'Google Gemini derzeit nicht erreichbar'

        except:
            news_reduktion = 'Google Gemini derzeit nicht erreichbar'
        
        news_reduktion = news_reduktion.replace(',', '<br>').strip()

        # update class attributes
        self.sent_dict['news'] = news
        self.sent_dict['news_red'] = news_reduktion
        self.sent_dict['empfehlung'] = empfehlung

    def update(self, tickername):
        """
        Aktualisiere beide analyse Methoden ( news_sentiment + prognose_kurs )

        :param - tickername: offzielles Kuerzel wievon yFinance verwendet
        :return - keine (Ergebnisse werden auf Attribute geschrieben)
        """
        self.news_sentiment(tickername)
        self.prognose_kurs(tickername)


    def get_sentiment(self):
        """
        Zugriffsfunktion für Attribute der News-Methode

        :param - 
        :return: empfehlung, news_reduktion
            - empfehlung: Stichwort: Verkaufen, Halten oder Kaufen
            - news_reduktion: 10 Stichwörter, auf denen die News-Empfehlung basiert
        """
        empfehlung = self.sent_dict['empfehlung']
        news_reduktion = self.sent_dict['news_red']

        return empfehlung, news_reduktion

    def get_prediction(self):
        """
        Zugriffsfunktion für Attribute der Vorhersage-Methode

        :param - 
        :return - pred_data, predictions, pred_days
            - pred_data: data frame mit Kursverlauf, auf dem die Vorhersage basiert
            - predictions: liste mit vorhergesagten Kurswerte
            - pred_days: liste mit Tagen für die vorhergesagten Kurswerte
        """

        # update class attributes
        pred_data = self.pred_dict['hist_data']
        predictions = self.pred_dict['pred']['Tage']
        pred_days = self.pred_dict['pred']['Werte']

        return pred_data, predictions, pred_days
    


if __name__ == "__main__":

    """
        Test funktion
    """
    # Erstelle eine Instanz der Klasse
    pa = prognose_analyse()

    # Beispiel-Ticker Apple
    ticker = "AAPL"  

    # Berechnung der Prognose
    pa.prognose_kurs(ticker)    
    pa.news_sentiment(ticker)

    # Konsolenausgabe
    print(pa.get_prediction())
    print(pa.get_sentiment())