## Verbesserungen / Erweiterungen

### Allgemein

- [ ] Exception Logging: alle Exceptions: except Exception: logging.exception -> Max
- [ ] alle session_states dokumentieren -> Max
- [ ] session.state als Konstanten zentral in Klasse definiert, nicht als string lokal gesetzt (Wartbarkeit) -> jeder für eigene Dateien
- [ ] Code umfangreich kommentieren (Kommentar-Kopf) -> jeder für eigene Datein
- [x] Objektorientiert Portfolio
- [x] Objektorientiert? statt Funktionen aufrufen
- [x] Requirements.txt reparieren?
- [ ] !! Requirements.txt aktualisieren (pip freeze)
- [ ] Optional: Dedizierte Calculations Klasse, convert to euro dynamisch Währungspaar und Interval
- [ ] !! Python Linter drüber laufen lassen
- [ ] Optional: yfinance log-errors (YF.download() has changed argument auto_adjust default to True & Calling float on a single element Series is deprecated and will raise a TypeError in the future. Use float(ser.iloc[0]) instead return float(data_before["Close"].iloc[-1]))
- [ ] Bugs suchen und auf Log-Errors überprüfen -> alle
- [ ] Quellen hinzufügen -> alle

### Authentifizierung

- [x] Registrierungen: Auf Email-Syntax überprüfen
- [x] Registrierungspage: copy paste auf dedizierte page und button einfügen
- [x] User-Session über Reload persistent (auth.json)

### Aktien Analyse

- [x] Dashboard grafisch besser strukturieren / UI optimierung
- [x] Indikatoren einarbeiten (Gleitender Durchschnitt 50, 200, RSI, MACD)
- [x] Fehlermeldung Indikatoren, wenn Datenpunkte nicht ausreichen
- [x] Zeit-Periode: YTD - Workaround benötigt, nicht direkt abrufbar

### Portfolio

- [x] Portfolio: Anzeige ändert sich nicht, wenn man den Button "Kaufpreis manuell" auswählt
- [x] Button/Funktion: Neues Portfolio Element hinzufügen
- [x] Button: Aus Portfolio-Element Ansicht zurück zu Aktien-Ansicht ohne Logout
- [x] Nach neu hinzugefügten Asset Formular zurücksetzen
- [ ] Neues Asset: Automatisch Preis anzeigen, aktualisieren wenn Datum geändert, für Input sperren wenn mode: automatisch, entsperren mode: manuell -> Maxim
- [ ] Tabelle Assets: Datum hinzufügen, sonst bei den identischen Assets nur Kurs als Unterscheidungsmerkmal -> Gregor
- [ ] Portfolio löschen und neues Portfolio anlegen: neue UUID?, ABER in Tabelle einfach durchnummeriert, beim löschen rücken höhere Portfolios nach / oder generell IDs in Datenbank aktualisieren -> Gregor
- [ ] Wertentwicklung über die Zeit: Sum Gesamtes Kapital + Verlauf in Grafik + %-Veränderung -> Gregor / Maxim

### Sentiment-Analyse

- [x] Sentimentanalyse: teil der news mit angeben
- [x] Prognose: Linie/Kursziel plotten

## Doku

- [ ] README
- [ ] requirements.txt