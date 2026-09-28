"""Fixtures partagées.

Principe : les composants déterministes (loaders, découpage, métadonnées,
recherche) sont testés SANS Ollama, grâce à un faux modèle d'embeddings.
"""

from __future__ import annotations

import dataclasses
import hashlib
import math
import re
import sys
from pathlib import Path

import pytest
from langchain_core.embeddings import Embeddings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from generate_corpus import generate_corpus  # noqa: E402

from app.config import Settings, load_settings  # noqa: E402


class KeywordEmbeddings(Embeddings):
    """Faux modèle d'embeddings : un "sac de mots" haché dans 256 dimensions.

    Il ne comprend pas le sens (pas de synonymes), mais deux textes qui
    partagent des mots ont des vecteurs proches : suffisant pour tester la
    mécanique de recherche, de façon rapide et reproductible.
    """

    dimensions = 256

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in re.findall(r"\w{3,}", text.lower()):
            bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dimensions
            vector[bucket] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


@pytest.fixture(scope="session")
def corpus_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Génère le corpus fictif dans un dossier temporaire."""
    data_dir = tmp_path_factory.mktemp("data")
    generate_corpus(data_dir)
    return data_dir


@pytest.fixture
def settings(corpus_dir: Path, tmp_path: Path) -> Settings:
    """Configuration pointant vers le corpus de test et un index temporaire."""
    return dataclasses.replace(
        load_settings(),
        data_dir=corpus_dir,
        chroma_dir=tmp_path / "chroma",
        collection_name="test_docs",
        min_score=0.0,
    )


@pytest.fixture
def embeddings() -> Embeddings:
    return KeywordEmbeddings()
