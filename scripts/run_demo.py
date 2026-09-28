"""Pose les questions de démonstration à l'agent, sans interaction.

    python scripts/run_demo.py

Utile pour comparer deux prompts, deux modèles ou deux réglages de retrieval
sur les mêmes questions (voir examples/evaluation.md).
"""

from __future__ import annotations

import sys
import time
from contextlib import nullcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langfuse import propagate_attributes  # noqa: E402

from app.agent import ask, create_documentation_agent  # noqa: E402
from app.config import check_ollama, load_settings  # noqa: E402
from app.observability import flush_traces, get_langfuse_handler  # noqa: E402
from app.retrieval import load_vector_store  # noqa: E402

DEMO_QUESTIONS = [
    "Quelle est la politique de télétravail ?",
    "Quel est le montant maximum remboursable pour un repas professionnel ?",
    "Quelles sont les règles de télétravail et quelles règles de sécurité dois-je respecter ?",
    "Quelle est la politique concernant les véhicules de fonction ?",
    "Combien de jours de congés sont prévus par la politique de l'entreprise ?",
]


def main() -> None:
    settings = load_settings()
    check_ollama(settings)
    agent = create_documentation_agent(settings, load_vector_store(settings))
    handler = get_langfuse_handler(settings)

    for question in sys.argv[1:] or DEMO_QUESTIONS:
        start = time.perf_counter()
        context = propagate_attributes(tags=["demo"]) if handler else nullcontext()
        with context:
            answer = ask(agent, question, callbacks=[handler] if handler else [])
        duration = time.perf_counter() - start
        print("=" * 80)
        print(f"Q : {question}")
        print(f"({answer.tool_calls} appel(s) d'outil, {duration:.1f} s)\n")
        print(answer.text)
        print("\nPassages consultés :", "; ".join(answer.sources) or "aucun")

    if handler:
        flush_traces()


if __name__ == "__main__":
    main()
