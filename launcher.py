"""Startpunkt för den färdiga appen (byggs med PyInstaller till JobbSok.exe).

Startar Streamlit-servern lokalt och öppnar webbläsaren. Ingen Python behövs på datorn.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

PORT = int(os.environ.get("JOBBSOK_PORT", "8501"))


def _oppna_webblasare() -> None:
    time.sleep(3)  # ge servern tid att starta
    webbrowser.open(f"http://localhost:{PORT}")


def main() -> None:
    from streamlit.web import cli as stcli

    bundle = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    app_fil = bundle / "app.py"
    threading.Thread(target=_oppna_webblasare, daemon=True).start()
    # Samma väg som kommandot "streamlit run app.py"
    sys.argv = [
        "streamlit", "run", str(app_fil),
        "--server.port", str(PORT),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--global.developmentMode", "false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
