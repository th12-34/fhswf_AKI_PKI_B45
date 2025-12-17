## fhswf_AKI_PKI_B45
#### Repo fuer die gemeinsame Programmieraufgabe in Python

### Prerequisites
API-Credentials für Gemini als Umgebungsvariable bereitstellen (app.py: GEMINI_API_KEY = os.getenv("GEMINI_API_KEY"))

| OS    | Befehl |
|-------|--------|
| Linux | `export GEMINI_API_KEY="key"` |
| PowerShell | `$env:GEMINI_API_KEY="key"` |

### Start
1. python3 -m venv pki-env
2. Environment aktivieren (siehe Tabelle)
3. pip install -r requirements.txt
4. python3 -m streamlit run app.py

| OS    | Befehl |
|-------|--------|
| Linux/macOS Bash/Zsh | `source pki-env/bin/activate` |
| Windows | `pki-env\Scripts\activate` |
| PowerShell | `pki-env\Scripts\Activate.ps1` |

Ausgabe:
      👋 Welcome to Streamlit!

      If you'd like to receive helpful onboarding emails, news, offers, promotions,
      and the occasional swag, please enter your email address below. Otherwise,
      leave this field blank.

Enter drücken--> Browser wird geöffnet


You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501

### Updates

- pip freeze > requirements.txt