# fhswf_AKI_PKI_B45

**Repository für die gemeinsame Programmieraufgabe in Python**

---

## Projektbeschreibung

### Zielsetzung

Entwicklung einer webbasierten Anwendung zur Analyse von Finanzdaten. Ziel ist es, technische Indikatoren zu visualisieren und KI-gestützte Prognosen mithilfe der Gemini-API zu erstellen.

### Aufbau des Projekts

Das Projekt ist modular in eine Streamlit-Oberfläche (Frontend) und verschiedene Logik-Klassen (Backend) unterteilt. Die Architektur trennt Datenverarbeitung, Authentifizierung und grafische Aufbereitung der Indikatoren.

---

## Installation und Start

### 1. Voraussetzungen

Für die Nutzung der Analyse-Funktionen müssen die API-Credentials für Gemini bereitgestellt werden.

> **Hinweis zur API-Key Priorisierung:**  
> Die Anwendung prüft primär die Umgebungsvariable des Betriebssystems. Ein beim Login hinterlegter API-Key wird nur verwendet, wenn keine globale Umgebungsvariable vorhanden ist.

| Betriebssystem | Befehl |
| --- | --- |
| Linux / macOS | `export GEMINI_API_KEY="key"` |
| Windows (PowerShell) | `$env:GEMINI_API_KEY="key"` |
| Windows (CMD) | `set GEMINI_API_KEY="key"` |

### 2. Durchführung

```bash
python3 -m venv pki-env
source pki-env/bin/activate   # Linux / macOS
pip install -r requirements.txt
streamlit run app.py
```

Die Anwendung ist anschließend unter http://localhost:8501 erreichbar.

---

## Technische Details

### Zentrale Konfiguration (`Config`)

**Autor:** Bastian Pivarcsi  
**Datum:** 13.01.2026

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

## Aufgabenverteilung

- **Basti:** Systemdesign, Datenbank, Portfolio-Klassen, Profile Page  
- **Gregor:** UI (TBD)  
- **Max:** Indikatoren (MA, RSI, MACD), Sidebar, Layout, Authentifizierung  
- **Maxim:** Portfolio-Optimierung (TBD)  
- **Thorben Herfeld:** Prognose & Analyse, Streamlit-Integration, Architektur

---

## Verbesserungen / Erweiterungen

### Allgemein & Code-Qualität

- [ ] Exception Logging (`logging.exception`)
- [ ] Session-State Dokumentation
- [x] Objektorientierte Portfolio-Struktur
- [x] Kommentierung & Header
- [ ] Linter & Bugfixing

### Authentifizierung & Analyse

- [x] E-Mail Validierung
- [x] Registrierungsseite
- [x] Persistente Sessions
- [x] Technische Indikatoren
- [x] Dashboard-Optimierung

### Portfolio & Prognose

- [ ] Wertentwicklungs-Visualisierung
- [ ] Portfolio-Optimierung
- [x] Sentiment-Analyse
- [x] Kursprognosen

---

## Dokumentation & Quellen

- Streamlit
- Google Gemini API
- ChatGPT
