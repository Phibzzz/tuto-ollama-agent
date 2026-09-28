"""Interface en ligne de commande.

    python -m app.cli
"""

from __future__ import annotations

import uuid
from contextlib import nullcontext

import httpx
import ollama
from langfuse import propagate_attributes

from app.agent import AgentAnswer, ask, create_documentation_agent
from app.config import OllamaNotReadyError, check_ollama, load_settings
from app.observability import flush_traces, get_langfuse_handler
from app.retrieval import IndexNotFoundError, load_vector_store

BANNER = """
====================================
 ACME - Documentation Assistant
====================================
Posez votre question (ou 'quit' pour quitter).
"""

EXIT_COMMANDS = {"quit", "exit", "q"}


def print_answer(answer: AgentAnswer) -> None:
    print(f"\nAgent :\n{answer.text}\n")
    if answer.sources:
        # Sources extraites des métadonnées des passages consultés par l'outil.
        print("Passages consultés (métadonnées) :")
        for source in answer.sources:
            print(f"- {source}")
    else:
        print("(Aucun passage documentaire consulté.)")
    print()


def main() -> None:
    settings = load_settings()

    # 1. Vérifications au démarrage : messages clairs plutôt que stack traces.
    try:
        check_ollama(settings)
        vector_store = load_vector_store(settings)
    except (OllamaNotReadyError, IndexNotFoundError) as error:
        raise SystemExit(f"Erreur : {error}")

    # 2. Assemblage de l'agent et du monitoring.
    agent = create_documentation_agent(settings, vector_store)
    langfuse_handler = get_langfuse_handler(settings)
    callbacks = [langfuse_handler] if langfuse_handler else []
    session_id = str(uuid.uuid4())  # regroupe les questions de cette session dans Langfuse

    print(BANNER)
    print(f"Modèle : {settings.ollama_model} | Embeddings : {settings.ollama_embedding_model}\n")

    # 3. Boucle question -> réponse.
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            continue
        if question.lower() in EXIT_COMMANDS:
            break

        # propagate_attributes (Langfuse v4) : ajoute session et tags à la trace.
        trace_context = (
            propagate_attributes(session_id=session_id, tags=["tutoriel", "cli"])
            if langfuse_handler
            else nullcontext()
        )
        try:
            with trace_context:
                answer = ask(agent, question, callbacks=callbacks)
            print_answer(answer)
        except (ConnectionError, httpx.ConnectError):
            print("\nErreur : Ollama ne répond plus. Vérifiez qu'il est lancé (`ollama serve`).\n")
        except ollama.ResponseError as error:
            print(f"\nErreur renvoyée par Ollama : {error.error}\n")

    if langfuse_handler:
        flush_traces()  # sinon les dernières traces peuvent être perdues à la sortie
    print("Au revoir !")


if __name__ == "__main__":
    main()
