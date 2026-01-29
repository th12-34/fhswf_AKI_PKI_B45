## Verbesserungen / Erweiterungen
# Code Freeze 29.01 
### Allgemein

- [-] Exception Logging: alle Exceptions: except Exception: logging.exception -> Max
- [x] alle session_states dokumentieren -> Max
- [x] session.state als Konstanten zentral in Klasse definiert, nicht als string lokal gesetzt (Wartbarkeit) -> jeder für eigene Dateien
- [x] Code umfangreich kommentieren (Kommentar-Kopf) -> jeder für eigene Dateien
- [x] Objektorientiert Portfolio
- [x] Objektorientiert? statt Funktionen aufrufen
- [x] Requirements.txt reparieren?
- [x] Requirements.txt aktualisieren (pip freeze)
- [x] Optional: Dedizierte Calculations Klasse, convert to euro dynamisch Währungspaar und Interval (portfolio_view)
- [x] Optional: Dedizierte Calculations Klasse, convert to euro dynamisch Währungspaar und Interval (dashboard) -> Max
- [x] !! Python Linter drüber laufen lassen -> Gregor, Maxim
- [ ] Optional: yfinance log-errors (YF.download() has changed argument auto_adjust default to True & Calling float on a single element Series is deprecated and will raise a TypeError in the future. Use float(ser.iloc[0]) instead return float(data_before["Close"].iloc[-1])) -> Thorben
- [x] Bugs suchen und auf Log-Errors überprüfen -> alle
- [x] Quellen hinzufügen -> alle
- [x] Autoren in Dateien anpassen -> alle
- [x] Ordner / Dateistruktur aufräumen
- [x] optional: profiländerung: ist und neues separat anzeigen (info und change)
- [x] portfolio übersicht: firmenname statt tickername (aus marktanalyse) -> gregor
- [x] optional: umbennen: page marktanalyse -> assetanalyse
- [x] Recherche Marktanalyse metriken an gewählten zeitraum anpassen (copy paste aus analyse) -> Maxim
- [x] portfolio-übersicht: hinzufügen historisches datum: kaufpreis wird nicht angepasst -> Maxim
- [x] portfolio-übersicht: prozentualen wachstum einheitlich anzeigen -> Maxim
- [x] optional Automatscihe Test cases?

### Authentifizierung

- [x] Registrierungen: Auf Email-Syntax überprüfen
- [x] Registrierungspage: copy paste auf dedizierte page und button einfügen
- [x] User-Session über Reload persistent (auth.json)
[text](http://localhost:8501/)
### Aktien Analyse

- [x] Dashboard grafisch besser strukturieren / UI optimierung
- [x] Indikatoren einarbeiten (Gleitender Durchschnitt 50, 200, RSI, MACD)
- [x] Fehlermeldung Indikatoren, wenn Datenpunkte nicht ausreichen
- [x] Zeit-Periode: YTD - Workaround benötigt, nicht direkt abrufbar
- [x] Vergleich verschiedene Verläufe/Assets (neue Page) -> Gregor

### Portfolio

- [x] Portfolio: Anzeige ändert sich nicht, wenn man den Button "Kaufpreis manuell" auswählt
- [x] Button/Funktion: Neues Portfolio Element hinzufügen
- [x] Button: Aus Portfolio-Element Ansicht zurück zu Aktien-Ansicht ohne Logout
- [x] Nach neu hinzugefügten Asset Formular zurücksetzen
- [x] Neues Asset: Automatisch Preis anzeigen, aktualisieren wenn Datum geändert, für Input sperren wenn mode: automatisch, entsperren mode: manuell -> Maxim
- [x] Tabelle Assets: Datum hinzufügen, sonst bei den identischen Assets nur Kurs als Unterscheidungsmerkmal -> Gregor
- [x] Portfolio löschen und neues Portfolio anlegen: neue UUID?, ABER in Tabelle einfach durchnummeriert, beim löschen rücken höhere Portfolios nach / oder generell IDs in Datenbank aktualisieren -> Gregor
- [x] Wertentwicklung über die Zeit: Sum Gesamtes Kapital + Verlauf in Grafik + %-Veränderung -> Maxim

### Sentiment-Analyse

- [x] Sentimentanalyse: teil der news mit angeben
- [x] Prognose: Linie/Kursziel plotten

## Doku / Abschluss

- [x] !! Python Linter drüber laufen lassen -> Gregor, Maxim
- [ ] README -> Test-Case -> Gregor
- [x] requirements.txt
- [ ] Fertiges Abgabepaket schnueren
- [x] install req in jungfräulichem VirtEnv Testen
- [ ] to-do.md löschen
- [ ] Projekt hochladen
