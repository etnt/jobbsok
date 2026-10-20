# JobbSök

Lokal app för att hitta jobb i Sverige, heltid, deltid eller tillfälligt. Körs på din egen dator.

## Installation (Windows)

Ingen Python behövs. Du behöver:

- Windows 10 eller 11 (64-bit)
- Internetanslutning
- En OpenRouter-nyckel (skapas på openrouter.ai)

1. Hämta den senaste zip-filen `JobbSok-vX.Y.Z-windows.zip` under **Releases** på GitHub.
2. Packa upp den i en mapp, t.ex. `C:\JobbSok`.
3. Kopiera `.env.example` till `.env` och skriv in OpenRouter-nyckeln.
4. Dubbelklicka på `JobbSok.exe`. Webbläsaren öppnas på http://localhost:8501.

Mer om detta, inklusive SmartScreen-varningen, finns i `LASMIG.txt` i zip-filen.

## Användning

- **Min profil:** fyll i uppgifter och klistra in CV-texten.
- **Sökinställningar:** orter, avstånd och antal timmar per vecka.
- **Sök jobb:** söker i Platsbanken inom valt avstånd. Alla jobb visas som standard.
  Under Sökinställningar kan du kryssa i "Bara deltid och tillfälliga jobb". Spara eller dölj annonser.
- **Bedöm med AI:** poängsätter annonser mot profilen (0–100) med en kort
  motivering och varningar. Max 25 annonser per klick. Kontaktuppgifter
  skickas aldrig till AI-modellen.
- **Mina ansökningar:** följ upp ansökningar med status (Ansökt, Intervju,
  Inget svar, Avslag), datum, anteckningar och påminnelser. Ansökningar med
  sista dag inom 3 dagar eller utan svar på 14 dagar markeras.
- **CV och brev:** välj en annons och skapa CV och personligt brev med AI.
  Språket följer annonsen (engelska om annonsen är på engelska, annars svenska).
  Redigera texten och ladda ner som Word-filer. Kontrollera alltid fakta innan
  du skickar. AI kan ibland skriva något som inte stämmer.

Sökningen använder Arbetsförmedlingens öppna API (ingen nyckel krävs) och
OpenStreetMap för att hitta koordinater till orter.

Data sparas i:

- **Installerad app (zip):** `%APPDATA%\JobbSok\data`. Filen `.env` ligger bredvid `JobbSok.exe`.
- **Från källkod:** mappen `data/` i projektmappen. Filen `.env` ligger i projektmappen.

Byta datamapp: sätt `JOBBSOK_DATA` i `.env`, t.ex. `JOBBSOK_DATA=C:\Users\DittNamn\JobbSok\data`.
Värdet i `.env` har företräde framför en eventuell variabel i terminalen.

Personnummer lagras aldrig.

## Utveckling (från källkod)

Kräver Python 3.11 eller nyare och git. Användare av den färdiga zip-filen behöver inte detta.

Windows:
1. Dubbelklicka på `starta.bat`. Första körningen skapar en virtuell miljö och installerar det som behövs.

macOS/Linux:
```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest
.venv/bin/streamlit run app.py
```

Bygga Windows-programmet lokalt: `pip install -r requirements-build.txt`, sedan PyInstaller enligt
`.github/workflows/release.yml`. Publicering sker automatiskt när en tagg som `v1.0.2` pushas.

## Inspiration

[MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search)

## Licence

MPL-2.0
