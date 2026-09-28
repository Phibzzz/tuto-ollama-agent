"""Tests de l'outil et de l'agent.

Les tests de l'outil n'utilisent pas de LLM : on appelle l'outil directement,
comme le ferait l'agent. Seul le dernier test (marqueur `ollama`) utilise le
vrai modèle ; il est exclu par défaut : `pytest -m ollama` pour le lancer.
"""

import pytest
from langchain_core.messages import ToolMessage

from app.agent import extract_sources
from app.ingestion import load_documents, split_documents
from app.retrieval import create_vector_store
from app.tools import NO_RESULT_MESSAGE, make_search_tool


@pytest.fixture
def search_tool(settings, embeddings):
    store = create_vector_store(settings, embeddings)
    store.add_documents(split_documents(load_documents(settings.data_dir)))
    return make_search_tool(store, k=2)


def test_tool_is_described_for_the_llm(search_tool) -> None:
    # Voilà ce que le LLM "voit" de l'outil : un nom, une description, des arguments.
    assert search_tool.name == "search_company_documents"
    assert "ACME" in search_tool.description
    assert set(search_tool.args) == {"query"}


def test_tool_returns_text_and_documents(search_tool) -> None:
    # Appel au format "tool call", comme le ferait l'agent -> renvoie un ToolMessage.
    message = search_tool.invoke(
        {"type": "tool_call", "id": "1", "name": search_tool.name, "args": {"query": "plafond repas"}}
    )

    assert isinstance(message, ToolMessage)
    assert "Source : frais-professionnels.xlsx" in message.content  # vu par le LLM
    assert message.artifact[0].metadata["sheet"] == "Barèmes"  # réservé à notre code


def test_tool_without_result(settings, embeddings) -> None:
    empty_store = create_vector_store(settings, embeddings)
    tool = make_search_tool(empty_store)

    message = tool.invoke({"type": "tool_call", "id": "1", "name": tool.name, "args": {"query": "x"}})
    assert message.content == NO_RESULT_MESSAGE
    assert message.artifact == []


def test_extract_sources_reads_artifacts(search_tool) -> None:
    message = search_tool.invoke(
        {"type": "tool_call", "id": "1", "name": search_tool.name, "args": {"query": "plafond repas"}}
    )
    sources, tool_calls = extract_sources([message])

    assert tool_calls == 1
    assert sources[0].startswith("frais-professionnels.xlsx, feuille « Barèmes »")


@pytest.mark.ollama
def test_agent_answers_with_real_model() -> None:
    """Test d'intégration : nécessite Ollama et l'index (python -m app.ingestion)."""
    from app.agent import ask, create_documentation_agent
    from app.config import OllamaNotReadyError, check_ollama, load_settings
    from app.retrieval import IndexNotFoundError, load_vector_store

    settings = load_settings()
    try:
        check_ollama(settings)
        store = load_vector_store(settings)
    except (OllamaNotReadyError, IndexNotFoundError) as error:
        pytest.skip(str(error))

    answer = ask(create_documentation_agent(settings, store), "Plafond d'un repas professionnel ?")

    # On teste ce qui est déterministe (l'outil a été appelé, la bonne source
    # a été consultée), pas la formulation exacte du LLM.
    assert answer.tool_calls >= 1
    assert any("frais-professionnels.xlsx" in source for source in answer.sources)
