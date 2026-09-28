"""Outils exposés à l'agent.

Un outil (tool) = une fonction Python + un nom + une description + un schéma
d'arguments. Le LLM ne lit PAS le code : il ne voit que le nom, la docstring et
les paramètres. C'est sur cette base qu'il décide d'appeler l'outil.

    Agent -> Tool -> Retriever -> Vector store -> Documents
"""

from __future__ import annotations

from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.tools import BaseTool

from app.retrieval import format_source, search_documents

NO_RESULT_MESSAGE = (
    "Aucun document pertinent trouvé dans la documentation ACME pour cette requête."
)


def format_results(results: list[tuple[Document, float]]) -> str:
    """Met en forme les passages pour le LLM, chacun avec sa source.

    Le score n'est pas transmis : il n'aide pas le LLM, qui a tendance à le recopier.
    """
    blocks = []
    for number, (document, _score) in enumerate(results, start=1):
        blocks.append(
            f"--- Passage {number} ---\n"
            f"Source : {format_source(document)}\n"
            f"Contenu : {document.page_content.strip()}"
        )
    return "\n\n".join(blocks)


def make_search_tool(vector_store: Chroma, k: int = 4, min_score: float = 0.0) -> BaseTool:
    """Crée l'outil de recherche, relié à un vector store donné.

    On utilise une fonction "fabrique" pour que l'outil connaisse le vector
    store sans variable globale (et pour pouvoir le tester avec un faux store).
    """

    # response_format="content_and_artifact" : l'outil retourne un tuple
    #   - content  : le texte envoyé au LLM
    #   - artifact : les objets Document bruts, NON envoyés au LLM, mais
    #                récupérables par notre code pour afficher des sources fiables.
    @tool("search_company_documents", response_format="content_and_artifact")
    def search_company_documents(query: str) -> tuple[str, list[Document]]:
        """Recherche dans la documentation interne de l'entreprise ACME
        (RH, congés, télétravail, sécurité informatique, frais professionnels,
        achats, règlement intérieur). Utilise cet outil pour toute question sur
        les règles ou politiques d'ACME. `query` est une requête courte en français.
        """
        results = search_documents(vector_store, query, k=k, min_score=min_score)
        if not results:
            return NO_RESULT_MESSAGE, []
        documents = [document for document, _score in results]
        return format_results(results), documents

    return search_company_documents
