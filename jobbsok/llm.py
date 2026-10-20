"""Anrop till AI-modeller via OpenRouter (OpenAI-kompatibelt API)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

API_URL = "https://openrouter.ai/api/v1/chat/completions"
APP_TITEL = "JobbSok"


class LLMFel(Exception):
    """Fel med ett användarvänligt meddelande på svenska."""


class LLMFatalFel(LLMFel):
    """Fel som inte blir bättre av nya försök (fel nyckel, slut på krediter, fel modell)."""


def api_nyckel() -> str | None:
    return os.environ.get("OPENROUTER_API_KEY") or None


def chat(
    messages: list[dict[str, str]],
    model: str,
    *,
    json_format: bool = False,
    temperature: float = 0.2,
    max_tokens: int = 800,
    api_key: str | None = None,
) -> str:
    """Skickar en chatt-förfrågan och returnerar svarets text."""
    key = api_key or api_nyckel()
    if not key:
        raise LLMFatalFel("Ingen OpenRouter-nyckel hittad. Lägg in den i filen .env.")

    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_format:
        body["response_format"] = {"type": "json_object"}

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "X-Title": APP_TITEL,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as fel:
        meddelande = _forklara_http_fel(fel.code, fel.read().decode("utf-8", "replace"), model)
        typ = LLMFatalFel if fel.code in (401, 402, 404) else LLMFel
        raise typ(meddelande) from fel
    except urllib.error.URLError as fel:
        raise LLMFel(f"Kunde inte nå OpenRouter. Kontrollera internetanslutningen. ({fel.reason})") from fel

    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as fel:
        raise LLMFel(f"Oväntat svar från OpenRouter: {str(data)[:200]}") from fel


def _forklara_http_fel(kod: int, kropp: str, model: str) -> str:
    if kod == 401:
        return "OpenRouter-nyckeln godkändes inte (401). Kontrollera nyckeln i filen .env."
    if kod == 402:
        return "Slut på krediter hos OpenRouter (402). Lägg till pengar på kontot."
    if kod == 404:
        return f"Modellen '{model}' finns inte hos OpenRouter (404). Ändra modellnamnet under Inställningar för AI."
    if kod == 429:
        return "För många förfrågningar just nu (429). Vänta en stund och försök igen."
    return f"OpenRouter svarade med fel {kod}: {kropp[:200]}"


def parsa_json(text: str) -> dict[str, Any]:
    """Tolkar JSON från modellsvaret. Tar bort eventuella kodblock."""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    start, slut = t.find("{"), t.rfind("}")
    if start == -1 or slut == -1:
        raise LLMFel("Modellen svarade inte med JSON.")
    try:
        return json.loads(t[start : slut + 1])
    except json.JSONDecodeError as fel:
        raise LLMFel("Kunde inte tolka modellens JSON-svar.") from fel
