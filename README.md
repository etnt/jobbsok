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
- **Mina ansökningar:** följ upp ansökningar med status (Ansökt, Intervju, Inget svar, Avslag), datum, anteckningar och påminnelser. Ansökningar med sista dag inom 3 dagar eller utan svar på 14 dagar markeras.
- **CV och brev:** välj en annons och skapa CV och personligt brev med AI. Språket följer annonsen (engelska om annonsen är på engelska, annars svenska). Redigera texten och ladda ner som Word-filer.
  Kontrollera alltid fakta innan du skickar. AI kan ibland skriva något som inte stämmer.

Sökningen använder Arbetsförmedlingens öppna API (ingen nyckel krävs) och OpenStreetMap för att hitta koordinater till orter.

Data sparas i mappen `data/` i appmappen. Personnummer lagras aldrig.

**Byta datamapp:** sätt `JOBBSOK_DATA` i filen `.env`, t.ex. `JOBBSOK_DATA=C:\Users\DittNamn\JobbSok\data`. Om variabeln är tom eller saknas används `data/`. Variabeln i `.env` har företräde framför en eventuell variabel i terminalen, så kontrollera att du inte har en gammal inställning där.

## Utveckling

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest
.venv/bin/streamlit run app.py
```
