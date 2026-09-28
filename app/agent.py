"""Agent documentaire : LLM (Ollama) + instructions + outils.

    agent = modèle + system prompt + outils + boucle "raisonner -> appeler un outil -> répondre"

`create_agent` (LangChain v1) fournit cette boucle : le LLM décide s'il doit
appeler un outil, LangChain exécute l'outil, renvoie le résultat au LLM,
et ainsi de suite jusqu'à une réponse finale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_core.messages import ToolMessage
from langchain_ollama import ChatOllama

from app.config import Settings
from app.retrieval import format_source
from app.tools import make_search_tool

SYSTEM_PROMPT = """Tu es l'assistant documentaire interne de l'entreprise ACME.

Règles :
1. Réponds toujours en français.
2. Pour toute question sur ACME (RH, congés, télétravail, sécurité, frais, achats,
   règlement), appelle d'abord l'outil search_company_documents.
3. Lis chaque passage renvoyé. Une ligne de tableau Excel est une information
   valide (ex. "Plafond (EUR) : 25" signifie un plafond de 25 euros).
4. Rédige une réponse directe et complète, à partir des passages uniquement.
   N'invente rien.
5. Seulement si AUCUN passage ne répond à la question, dis :
   "Je n'ai pas trouvé cette information dans la documentation ACME."
6. Termine par "Sources :" suivi uniquement des sources des passages
   réellement utilisés (fichier, page ou feuille), recopiées depuis l'outil.
7. Signale toute connaissance générale qui ne vient pas des documents par
   "(connaissance générale, hors documentation)".
"""


def create_llm(settings: Settings) -> ChatOllama:
    """Le LLM local. temperature=0 : réponses plus stables, utile en démo."""
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )


def create_documentation_agent(settings: Settings, vector_store: Chroma):
    """Assemble le modèle, l'outil de recherche et les instructions."""
    search_tool = make_search_tool(vector_store, k=settings.top_k, min_score=settings.min_score)
    return create_agent(
        model=create_llm(settings),
        tools=[search_tool],
        system_prompt=SYSTEM_PROMPT,
    )


@dataclass
class AgentAnswer:
    text: str
    sources: list[str] = field(default_factory=list)  # passages réellement consultés
    tool_calls: int = 0


def extract_sources(messages: list[Any]) -> tuple[list[str], int]:
    """Relit l'historique de l'agent pour retrouver les documents consultés.

    Ces sources viennent des métadonnées (artifact des ToolMessage), pas du
    texte généré par le LLM : elles ne peuvent donc pas être inventées.
    """
    sources: list[str] = []
    tool_calls = 0
    for message in messages:
        if isinstance(message, ToolMessage):
            tool_calls += 1
            for document in message.artifact or []:
                label = format_source(document)
                if label not in sources:
                    sources.append(label)
    return sources, tool_calls


def ask(agent, question: str, callbacks: list | None = None) -> AgentAnswer:
    """Pose une question à l'agent et retourne la réponse + les sources."""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"callbacks": callbacks or [], "run_name": "acme-doc-agent"},
    )
    messages = result["messages"]
    sources, tool_calls = extract_sources(messages)
    return AgentAnswer(text=messages[-1].content, sources=sources, tool_calls=tool_calls)
