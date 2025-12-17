## fhswf_AKI_PKI_B45
#### Repo fuer die gemeinsame Programmieraufgabe in Python

### Pre-Requisites
API-Credentials für Gemini als Umgebungsvariable zur Verfügung stellen (app.py: GEMINI_API_KEY = os.getenv("GEMINI_API_KEY"))

Linux: export GEMINI_API_KEY="key"

PowerShell: $env:GEMINI_API_KEY="key"

### Start:
python3 -m venv pki-env

Linux/macOS Bash/Zsh: source pki-env/bin/activate

Windows Command Prompt:	pki-env\Scripts\activate

Windows PowerShell: pki-env\Scripts\Activate.ps1

pip install -r requirements.txt

python3 -m streamlit run app.py


Ausgabe:
      👋 Welcome to Streamlit!

      If you'd like to receive helpful onboarding emails, news, offers, promotions,
      and the occasional swag, please enter your email address below. Otherwise,
      leave this field blank.

Enter drücken--> Browser wird geöffnet


You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501

