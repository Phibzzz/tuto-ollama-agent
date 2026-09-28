"""Tests de recherche : requête -> documents pertinents (sans Ollama)."""

import pytest
from langchain_core.documents import Document

from app.ingestion import load_documents, split_documents
from app.retrieval import (
    IndexNotFoundError,
    create_vector_store,
    format_source,
    load_vector_store,
    search_documents,
)


@pytest.fixture
def vector_store(settings, embeddings):
    store = create_vector_store(settings, embeddings)
    store.add_documents(split_documents(load_documents(settings.data_dir)))
    return store


def test_meal_question_finds_excel_row(vector_store) -> None:
    results = search_documents(vector_store, "plafond repas professionnel", k=2)

    best_document, _score = results[0]
    assert best_document.metadata["source"] == "frais-professionnels.xlsx"
    assert best_document.metadata["sheet"] == "Barèmes"


def test_remote_work_question_finds_pdf(vector_store) -> None:
    results = search_documents(vector_store, "combien de jours de télétravail par semaine", k=2)

    assert results[0][0].metadata["source"] == "politique-teletravail.pdf"


def test_min_score_filters_everything_when_too_high(vector_store) -> None:
    assert search_documents(vector_store, "véhicule de fonction", k=4, min_score=0.99) == []


def test_load_vector_store_explains_missing_index(settings, embeddings) -> None:
    with pytest.raises(IndexNotFoundError, match="python -m app.ingestion"):
        load_vector_store(settings, embeddings)


def test_load_vector_store_opens_existing_index(settings, embeddings, vector_store) -> None:
    reopened = load_vector_store(settings, embeddings)
    assert reopened.get(limit=1)["ids"]


@pytest.mark.parametrize(
    ("metadata", "expected"),
    [
        ({"source": "conges.pdf", "page": 2}, "conges.pdf, page 2"),
        (
            {"source": "frais-professionnels.xlsx", "sheet": "Barèmes", "row": 2},
            "frais-professionnels.xlsx, feuille « Barèmes », ligne 2",
        ),
        ({"source": "notes.md"}, "notes.md"),  # ni page ni feuille : on n'invente rien
    ],
)
def test_format_source(metadata: dict, expected: str) -> None:
    assert format_source(Document(page_content="...", metadata=metadata)) == expected
