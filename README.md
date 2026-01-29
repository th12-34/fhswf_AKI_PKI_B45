# fhswf_AKI_PKI_B45

**Repository für die gemeinsame Programmieraufgabe in Python**

---

## 1. Projektbeschreibung

### 1.1 Zielsetzung

Entwicklung einer webbasierten Anwendung zur Analyse von Finanzdaten sowie der Hinterlegung eines einfachen Portfolios von Vermögenswerten. Ziel ist sind:

1. Marktanalysen durchzuführen: Technische Indikatoren zu visualisieren und KI-gestützte Prognosen mithilfe der Gemini-API zu erstellen.
2. Depotanalyse: Assets hinzufügen (Erwerb in real-time oder historisch) oder entfernen und das Gesamtportfolio tracken.

### 1.2 Aufbau des Projekts

Das Projekt ist modular aufgebaut und trennt Frontend (Streamlit Views), Backend-Logik (Controller/Service) und Datenhaltung.

**Kern-Komponenten:**
*   `app.py`: Einstiegspunkt der Anwendung, steuert die Navigation.
*   `databaseHandler.py`: Verwaltet die SQLite-Datenbank für Nutzer, Portfolios und Assets.
*   `portfolio_calculator.py`: Service-Klasse für Finanzberechnungen, API-Abrufe (yfinance) und Währungsumrechnungen.
*   `prognose_analyse.py`: Enthält die Logik für KI-gestützte Kursprognosen (ARIMA) und Sentiment-Analysen (Google Gemini).

**Portfolio-Management:**
*   `portfoliomanager.py`: Controller zur Steuerung von Portfolios (Erstellen, Löschen, Auswählen).
*   `portfolio.py`: Repräsentiert ein einzelnes Portfolio und dessen Gesamtwert.
*   `portfolioasset.py`: Datenklasse für einzelne Vermögenswerte (Aktien, Krypto, Cash).

**Views (Benutzeroberfläche):**
*   `view/asset_analyze.py`: Hauptansicht für Marktdaten, Charts und Indikatoren.
*   `view/asset_comparison.py`: Ermöglicht den direkten Vergleich zweier Assets auf absoluter und relativer Basis.
*   `view/portfolio_view.py`: Detaillierte Ansicht der eigenen Portfolios inkl. Performance-Historie.
*   `view/portfolios_manage.py`: Verwaltungsoberfläche zum Anlegen und Löschen von Portfolios.
*   `view/profile.py`: Verwaltungsoberfläche zum Ändern und Löschen eines Benutzerkontos.
---

## 2. Installation und Start

### 2.1 Voraussetzungen

Für die Nutzung der Analyse-Funktionen müssen die API-Credentials für Gemini bereitgestellt werden.

> **Hinweis zur API-Key Priorisierung:**  
> Die Anwendung prüft primär die Umgebungsvariable des Betriebssystems. Ein beim Login hinterlegter API-Key wird nur verwendet, wenn keine globale Umgebungsvariable vorhanden ist.

| Betriebssystem       | Befehl                        |
| -------------------- | ----------------------------- |
| Linux / macOS        | `export GEMINI_API_KEY="key"` |
| Windows (PowerShell) | `$env:GEMINI_API_KEY="key"`   |
| Windows (CMD)        | `set GEMINI_API_KEY="key"`    |

### 2.2 Durchführung

```bash
python3.13 -m venv pki-env
source pki-env/bin/activate   # Linux / macOS
pip install -r requirements.txt
streamlit run app.py
```

Die Anwendung ist anschließend unter http://localhost:8501 erreichbar.

---

## 3. Testfälle

Um die Funktionalität der Anwendung zu überprüfen, können folgende Szenarien durchgespielt werden:

### 3.1 Testfall 1: Marktanalyse & KI-Prognose
**Ziel:** Analyse einer Aktie mittels technischer Indikatoren und KI.

1.  Navigieren Sie im Menü zu **Asset-Analyse**.
2.  Geben Sie im Suchfeld einen Ticker ein (z. B. `AAPL` für Apple oder `BTC-EUR` für Bitcoin).
3.  **Technische Analyse:**
    *   Überprüfen Sie den Chartverlauf.
    *   Aktivieren Sie Indikatoren wie **MA20/50/200**, **RSI**, **MACD** und **Bollinger Bands** über die Toggle-Buttons.
4.  **KI-Prognose:**
    *   Öffnen Sie den Expander "Kursentwicklungsprognose & Handlungsempfehlung".
    *   Die Anwendung berechnet nun mittels **ARIMA** eine Kursprognose für die nächsten 14 Tage.
    *   Gleichzeitig analysiert **Google Gemini** aktuelle News und gibt eine Kauf-/Verkaufsempfehlung ("Sentiment") ab.
 
### 3.2 Testfall 2: Asset-Vergleich
**Ziel:** Absoluter sowie relativer Vergleich zweier Assets. 

1.  Navigieren Sie im Menü zu **Asset-Vergleich**.
2.  Geben Sie für Asset A sowie Asset B im Suchfeld einen Firmennamen, eine Aktie oder Krypto-Ticker ein (z. B. `AAPL` für Apple und `amazon` -> `AMZN` für Amazon).
3.  In Abhängigkeit von der gewählten Betrachtungsperiode lässt sich nun die **absolute sowie relative Performance von Asset A gegenüber Asset B vergleichen**. Zudem wird der relative Bestperformer beider Assets explizit veranschaulicht.
4.  Die Daten können bei Bedarf zu einem späteren Zeitpunkt neu geladen werden. Außerdem ist es möglich, einen Ausschnitt der verwendeten Daten einzusehen.

### 3.3 Testfall 3: Portfolio-Management (Login & Historischer Kauf)
**Ziel:** Erstellen eines Portfolios und Simulation eines historischen Kaufs.

1.  **Registrierung/Login:**
    *   Klicken Sie oben rechts auf "Gast" -> "Registrierung".
    *   Erstellen Sie einen Account (optional mit Gemini API Key).
    *   Loggen Sie sich ein.
2.  **Portfolio anlegen:**
    *   Navigieren Sie zu **Portfolio** -> **Verwaltung**.
    *   Erstellen Sie ein neues Portfolio (z. B. "Test-Depot").
3.  **Assets kaufen:**
    *   Wechseln Sie zu **Portfolio** -> **Übersicht**.
    *   Wählen Sie das erstellte Portfolio aus.
    *   Suchen Sie ein Asset (z. B. `NVDA`).
    *   Wählen Sie bei "Preis-Basis" die Option **Historisches Datum** (z. B. vor 6 Monaten).
    *   Fügen Sie das Asset hinzu.
4.  **Auswertung:**
    *   Das System berechnet automatisch den damaligen Kaufkurs und vergleicht ihn mit dem aktuellen Marktwert.
    *   Die Metriken "Gewinn" und "Gesamtwert" zeigen die Performance seit dem Kaufdatum an.

### 3.4 Testfall 4: Benutzerverwaltung
**Ziel:** Änderung der Benutzerdaten sowie Löschung des Benutzerkontos. 

1.  Navigieren Sie im Menü zu **Benutzereinstellungen**.
2.  In der vorliegenden View können Sie die hinterlegte E-Mail-Adresse, den Gemini-API-Key sowie Ihr Passwort ändern. Dabei werden leere Felder ignoriert und Änderungen unter Einhaltung der syntaktischen Voraussetzungen übernommen.
3.  Bei Bedarf ist es hier zudem möglich, das erstellte Konto zu löschen. 
---

## 4. Technische Details

### 4.1 Zentrale Konfiguration (`Config`)

Zentrale Verwaltung von Session-State-Keys und globalen Einstellungen.

```python
KEY_LOGGED_IN = "logged_in"
KEY_USERNAME = "username"
KEY_USER = "user"
KEY_AUTH_ERROR = "auth_error"
KEY_AUTH_INFO = "auth_info"

AUTH_FILE = "auth.json"
DATABASE_NAME = "user.db"
```

Zusätzliche Steuerungs-Keys:

- `show_snow`
- `last_auth_action`
- `show_ma`

---

## 5. Aufgabenverteilung

- **Bastian Pivarcsi:** Systemdesign, Datenbank, Portfolio-Klassen, Profile
- **Gregor A. D. Schumacher:** Asset-Vergleich, Profile, Bollinger Bands, UI, Refactoring
- **Maximilian Pfau:** Indikatoren (MA, RSI, MACD), Sidebar, Layout, Authentifizierung
- **Maxim Sein :** Portfolio-Optimierung: Berechnung, Verwaltung und Visualisierung, Prototyp Grundversion 
- **Thorben Herfeld:** Prognose & Analyse, Streamlit-Integration, Architektur

## 6. Dokumentation & Quellen

- https://yfinance.yahoofinance.com/
- https://docs.streamlit.io/
- https://plotly.com/python/
- https://pandas.pydata.org/pandas-docs/stable/user_guide/10min.html
- Lehrbrief "Python für alle"
- Google Gemini
- Google Gemini API
- ChatGPT
