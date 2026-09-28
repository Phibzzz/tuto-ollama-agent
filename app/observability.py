"""Monitoring avec Langfuse (SDK Python v4).

Langfuse s'intègre à LangChain via un callback handler : chaque étape exécutée
par LangChain (agent, appel LLM, appel d'outil) devient une observation dans
une trace Langfuse. Le SDK lit ses clés dans les variables d'environnement
LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY et LANGFUSE_BASE_URL.

Le monitoring est OPTIONNEL : sans clés, l'application fonctionne sans traces.
"""

from __future__ import annotations

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from app.config import Settings


def get_langfuse_handler(settings: Settings) -> CallbackHandler | None:
    """Retourne le handler Langfuse, ou None si Langfuse n'est pas utilisable."""
    if not settings.langfuse_enabled:
        print(
            "[langfuse] Non configuré (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY absents) : "
            "traçage désactivé."
        )
        return None

    try:
        # auth_check() fait un appel réseau : pratique en tutoriel pour détecter
        # tout de suite une mauvaise clé ou une mauvaise URL (à éviter en production).
        if not get_client().auth_check():
            raise RuntimeError("clés refusées")
    except Exception as error:
        # Les erreurs HTTP du SDK portent un status_code (401 = mauvaises clés ou mauvaise région)
        reason = getattr(error, "status_code", None) or type(error).__name__
        print(
            f"[langfuse] Connexion impossible à {settings.langfuse_base_url} ({reason}) : "
            "traçage désactivé.\n"
            "           Vérifiez les clés et LANGFUSE_BASE_URL (région EU/US) dans .env."
        )
        return None

    print(f"[langfuse] Traçage actif -> {settings.langfuse_base_url}")
    return CallbackHandler()


def flush_traces() -> None:
    """Envoie les traces en attente (le SDK les envoie par lots, en arrière-plan)."""
    get_client().flush()
