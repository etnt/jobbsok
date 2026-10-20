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
- **Sök jobb:** söker i Platsbanken inom valt avstånd. Deltid och tillfälliga jobb visas först. Spara eller dölj annonser.
- **Bedöm med AI:** poängsätter annonser mot profilen (0–100) med en kort motivering och varningar. Max 25 annonser per klick. Kontaktuppgifter skickas aldrig till AI-modellen.
- **Mina ansökningar:** kommer i nästa version.

Sökningen använder Arbetsförmedlingens öppna API (ingen nyckel krävs) och OpenStreetMap för att hitta koordinater till orter.

Data sparas i mappen `data/` i appmappen. Personnummer lagras aldrig.

## Utveckling

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest
.venv/bin/streamlit run app.py
```
