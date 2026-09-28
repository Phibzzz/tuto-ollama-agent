"""Étape 5 du tutoriel : tester la recherche SANS agent et SANS LLM.

    python scripts/search_demo.py "plafond repas professionnel"

Affiche les passages retrouvés, leur source et leur score de pertinence.
Si la recherche ne trouve pas les bons passages, l'agent ne pourra pas
bien répondre : on vérifie donc le retrieval séparément.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_settings  # noqa: E402
from app.retrieval import format_source, load_vector_store, search_documents  # noqa: E402


def main() -> None:
    query = " ".join(sys.argv[1:]) or "Quelle est la politique de télétravail ?"
    settings = load_settings()
    vector_store = load_vector_store(settings)

    print(f"Requête : {query}\n")
    for document, score in search_documents(vector_store, query, k=settings.top_k):
        print(f"[{score:.3f}] {format_source(document)}")
        print(f"        {document.page_content[:150].strip()!r}\n")


if __name__ == "__main__":
    main()
