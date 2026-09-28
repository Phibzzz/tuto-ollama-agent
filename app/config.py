"""Configuration de l'application, lue depuis le fichier .env.

Toute la configuration est centralisée ici : les autres modules reçoivent un
objet `Settings` au lieu de lire eux-mêmes les variables d'environnement.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import ollama
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# load_dotenv() copie les valeurs de .env dans os.environ.
# Le SDK Langfuse lit directement LANGFUSE_* dans os.environ : c'est pour cela
# que ces variables n'ont pas besoin d'être passées explicitement au SDK.
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str
    ollama_model: str
    ollama_embedding_model: str
    data_dir: Path
    chroma_dir: Path
    collection_name: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_score: float
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_base_url: str

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)


def load_settings() -> Settings:
    """Construit la configuration à partir des variables d'environnement."""
    return Settings(
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
        ollama_embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        data_dir=PROJECT_ROOT / os.getenv("DATA_DIR", "data"),
        chroma_dir=PROJECT_ROOT / os.getenv("CHROMA_DIR", ".chroma"),
        collection_name=os.getenv("CHROMA_COLLECTION", "acme_docs"),
        chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
        top_k=int(os.getenv("TOP_K", "4")),
        min_score=float(os.getenv("MIN_SCORE", "0.55")),
        langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
        langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
        langfuse_base_url=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
    )


class OllamaNotReadyError(RuntimeError):
    """Ollama ne répond pas, ou un modèle requis n'est pas téléchargé."""


def check_ollama(settings: Settings) -> None:
    """Vérifie qu'Ollama répond et que les deux modèles sont disponibles.

    On vérifie AVANT de lancer l'agent pour afficher un message clair,
    plutôt qu'une longue stack trace au milieu d'une réponse.
    """
    client = ollama.Client(host=settings.ollama_base_url)
    try:
        installed = {model.model for model in client.list().models}
    except (ConnectionError, ollama.ResponseError) as error:
        raise OllamaNotReadyError(
            f"Ollama est injoignable sur {settings.ollama_base_url}.\n"
            "  -> Lancez l'application Ollama ou `ollama serve`, puis réessayez."
        ) from error

    for model in (settings.ollama_model, settings.ollama_embedding_model):
        # "nomic-embed-text" est enregistré par Ollama sous "nomic-embed-text:latest"
        if model not in installed and f"{model}:latest" not in installed:
            raise OllamaNotReadyError(
                f"Le modèle Ollama '{model}' n'est pas installé.\n"
                f"  -> Téléchargez-le avec : ollama pull {model}"
            )
