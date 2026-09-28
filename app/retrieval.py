"""Retrieval : embeddings, vector store et recherche documentaire.

Recherche vectorielle en une phrase : chaque texte est transformé en vecteur
(liste de nombres) par un modèle d'embeddings. Deux textes proches par le sens
ont des vecteurs proches. Chercher = calculer le vecteur de la question, puis
retrouver les vecteurs de documents les plus proches.
"""

from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings

from app.config import Settings

SearchResult = tuple[Document, float]  # (document, score de pertinence entre 0 et 1)


class NomicEmbeddings(OllamaEmbeddings):
    """nomic-embed-text exige un préfixe indiquant la tâche (cf. sa fiche modèle).

    Le même texte n'est pas encodé de la même façon selon qu'il s'agit d'un
    document à indexer ou d'une question : sans préfixe, la recherche se dégrade.
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return super().embed_documents([f"search_document: {text}" for text in texts])

    def embed_query(self, text: str) -> list[float]:
        return super().embed_query(f"search_query: {text}")


def create_embeddings(settings: Settings) -> Embeddings:
    """Modèle d'embeddings local, servi par Ollama (différent du LLM !)."""
    model = settings.ollama_embedding_model
    embeddings_class = NomicEmbeddings if model.startswith("nomic-embed-text") else OllamaEmbeddings
    return embeddings_class(model=model, base_url=settings.ollama_base_url)


def create_vector_store(settings: Settings, embeddings: Embeddings) -> Chroma:
    """Vector store Chroma persisté sur disque (dossier .chroma/), sans serveur."""
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=embeddings,
        persist_directory=str(settings.chroma_dir),
        # distance cosinus -> scores de pertinence faciles à lire (1 = identique)
        collection_configuration={"hnsw": {"space": "cosine"}},
    )


class IndexNotFoundError(RuntimeError):
    """Le vector store n'existe pas encore ou est vide."""


def load_vector_store(settings: Settings, embeddings: Embeddings | None = None) -> Chroma:
    """Ouvre le vector store existant, ou explique comment le créer."""
    missing_message = (
        f"Aucun index trouvé dans {settings.chroma_dir}.\n"
        "  -> Lancez d'abord l'ingestion : python -m app.ingestion"
    )
    if not settings.chroma_dir.exists():
        raise IndexNotFoundError(missing_message)

    vector_store = create_vector_store(settings, embeddings or create_embeddings(settings))
    if not vector_store.get(limit=1)["ids"]:
        raise IndexNotFoundError(missing_message)
    return vector_store


def search_documents(
    vector_store: Chroma, query: str, k: int = 4, min_score: float = 0.0
) -> list[SearchResult]:
    """Retourne les k passages les plus proches de la requête.

    Les passages sous `min_score` sont écartés : mieux vaut ne rien renvoyer
    au LLM qu'un passage hors sujet qu'il risquerait d'utiliser.
    """
    results = vector_store.similarity_search_with_relevance_scores(query, k=k)
    return [(document, score) for document, score in results if score >= min_score]


def format_source(document: Document) -> str:
    """Construit une référence lisible à partir des métadonnées DISPONIBLES.

    On n'affiche une page ou une feuille que si elle existe dans les
    métadonnées : on n'invente jamais une localisation.
    """
    metadata = document.metadata
    label = metadata.get("source", "source inconnue")
    if "page" in metadata:
        label += f", page {metadata['page']}"
    if "sheet" in metadata:
        label += f", feuille « {metadata['sheet']} »"
    if "row" in metadata:
        label += f", ligne {metadata['row']}"
    return label
