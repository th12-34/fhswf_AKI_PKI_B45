## Verbesserungen / Erweiterungen

### Allgemein

- [ ] Robuster machen; Tests, Fehlerabfragen, Rückmeldungen einbauen
- [ ] Code umfangreich kommentieren
- [x] Objektorientiert Portfolio
- [ ] Objektorientiert? statt Funktionen aufrufen
- [x] Requirements.txt reparieren?
- [ ] Performance verbessern
- [ ] Exception Logging
- [ ] Dedizierte Calculations Klasse, convert to euro dynamisch Währungspaar und Interval
- [ ] Python Linter drüber laufen lassen
- [ ] yfinance log-errors (YF.download() has changed argument auto_adjust default to True & Calling float on a single element Series is deprecated and will raise a TypeError in the future. Use float(ser.iloc[0]) instead return float(data_before["Close"].iloc[-1]))
- [ ] Generell auf Log-Errors überprüfen

### Authentifizierung

- [x] Registrierungen: Auf Email-Syntax überprüfen
- [x] Registrierungspage: copy paste auf dedizierte page und button einfügen
- [x] User-Session über Reload persistent (auth.json)
- [ ] Optional: Login/Registrierungsfeld fixe Breite

### Aktien Analyse

- [x] Dashboard grafisch besser strukturieren / UI optimierung
- [ ] Indikatoren einarbeiten (Gleitender Durchschnitt 50, 200, RSI, MACD)
- [x] Fehlermeldung Indikatoren, wenn Datenpunkte nicht ausreichen
- [x] Zeit-Periode: YTD - Workaround benötigt, nicht direkt abrufbar
- [ ] In Diagramm zoomen verändert nur x-Achse, nicht y-Achse (Ergebnis: waagerechter Strich)

### Portfolio

- [x] Portfolio: Anzeige ändert sich nicht, wenn man den Button "Kaufpreis manuell" auswählt
- [x] Button/Funktion: Neues Portfolio Element hinzufügen
- [x] Button: Aus Portfolio-Element Ansicht zurück zu Aktien-Ansicht ohne Logout
- [x] Nach neu hinzugefügten Asset Formular zurücksetzen
- [ ] Neues Asset: Automatisch Preis anzeigen, aktualisieren wenn Datum geändert, für Input sperren wenn mode: automatisch, entsperren mode: manuell
- [ ] Tabelle Assets: Datum hinzufügen, sonst bei den identischen Assets nur Kurs als Unterscheidungsmerkmal
- [ ] Portfolio löschen und neues Portfolio anlegen: neue UUID?, ABER in Tabelle einfach durchnummeriert, beim löschen rücken höhere Portfolios nach / oder generell IDs in Datenbank aktualisieren
- [ ] Wertentwicklung über die Zeit: Sum Gesamtes Kapital + Verlauf in Grafik + %-Veränderung

### Sentiment-Analyse

- [x] Sentimentanalyse: teil der news mit angeben
- [x] Prognose: Linie/Kursziel plotten

## Doku

- [ ] README
- [ ] UML
- [ ] requirements.txt
- [ ] Warum welche toolboxen?
- [ ] ADR: Architecture Design records
