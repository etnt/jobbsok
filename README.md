# JobbSök

Lokal app för att hitta tillfälliga och deltidsjobb. Körs på din egen dator.

## Installation (Windows)

1. Installera Python 3.11 eller nyare från python.org. Bocka i "Add python to PATH".
2. Kopiera `.env.example` till `.env` och skriv in OpenRouter-nyckeln.
3. Dubbelklicka på `starta.bat`. Första körningen installerar det som behövs.
4. Webbläsaren öppnas på http://localhost:8501.

## Användning

- **Min profil:** fyll i uppgifter och klistra in CV-texten.
- **Sökinställningar:** orter, avstånd och antal timmar per vecka.
- **Sök jobb:** kommer i nästa version (Platsbanken).
- **Mina ansökningar:** kommer i nästa version.

Data sparas i mappen `data/` i appmappen. Personnummer lagras aldrig.

## Utveckling

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest
.venv/bin/streamlit run app.py
```
