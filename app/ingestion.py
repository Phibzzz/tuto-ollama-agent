"""Ingestion : fichiers -> Documents LangChain -> chunks -> vector store.

Cette étape est exécutée UNE FOIS (ou à chaque modification du corpus),
indépendamment des questions des utilisateurs :

    python -m app.ingestion

Deux formats, deux traitements :
- PDF   : du texte semi-structuré, organisé en pages  -> 1 Document par page, puis découpage.
- Excel : des données tabulaires, organisées en lignes -> 1 Document par ligne, sans découpage.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.config import Settings, load_settings
from app.retrieval import create_embeddings, create_vector_store

# ---------------------------------------------------------------------------
# 1. Chargement PDF
# ---------------------------------------------------------------------------


def load_pdf(path: Path) -> list[Document]:
    """Extrait le texte d'un PDF : un Document LangChain par page.

    On utilise directement pypdf (PdfReader) : c'est la bibliothèque qu'utilisait
    l'ancien `PyPDFLoader` de langchain-community, package aujourd'hui en fin de vie.
    """
    try:
        reader = PdfReader(path)
        pages = [page.extract_text() or "" for page in reader.pages]
    except (PdfReadError, OSError, ValueError) as error:
        print(f"[ingestion] PDF illisible, ignoré : {path.name} ({error})")
        return []

    return [
        Document(
            page_content=text,
            # page est numérotée à partir de 1, comme dans un lecteur PDF
            metadata={"source": path.name, "page": number, "doc_type": "pdf"},
        )
        for number, text in enumerate(pages, start=1)
        if text.strip()  # une page vide (ou scannée, sans texte) n'apporte rien
    ]


# ---------------------------------------------------------------------------
# 2. Chargement Excel
# ---------------------------------------------------------------------------


def format_cell(value: object) -> str:
    """Affiche 25.0 comme 25, mais garde 0.35."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def dataframe_to_documents(df: pd.DataFrame, source: str, sheet: str) -> list[Document]:
    """Transforme chaque ligne d'un tableau en un petit texte autonome.

    Une ligne Excel n'a de sens qu'avec ses en-têtes : "25" seul ne veut rien
    dire, "Catégorie : Repas professionnel ; Plafond (EUR) : 25" oui.
    On répète donc les en-têtes dans chaque Document.
    """
    documents = []
    for index, row in df.iterrows():
        fields = [
            f"{column} : {format_cell(value)}"
            for column, value in row.items()
            if pd.notna(value)  # on ignore les cellules vides
        ]
        if not fields:
            continue
        documents.append(
            Document(
                page_content=f"Feuille « {sheet} » - " + " ; ".join(fields),
                metadata={
                    "source": source,
                    "sheet": sheet,
                    # index 0 = ligne 2 dans Excel (la ligne 1 contient les en-têtes)
                    "row": int(index) + 2,
                    "doc_type": "excel",
                },
            )
        )
    return documents


def load_excel(path: Path) -> list[Document]:
    """Lit toutes les feuilles d'un classeur avec pandas (moteur openpyxl)."""
    try:
        # sheet_name=None -> dictionnaire {nom de feuille: DataFrame}
        sheets = pd.read_excel(path, sheet_name=None, engine="openpyxl")
    except Exception as error:  # openpyxl lève des erreurs variées selon la corruption
        print(f"[ingestion] Excel invalide, ignoré : {path.name} ({error})")
        return []

    documents = []
    for sheet_name, df in sheets.items():
        documents.extend(dataframe_to_documents(df, source=path.name, sheet=sheet_name))
    return documents


# ---------------------------------------------------------------------------
# 3. Chargement texte / Markdown (optionnel)
# ---------------------------------------------------------------------------


def load_text(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8")
    return [Document(page_content=text, metadata={"source": path.name, "doc_type": "text"})]


# ---------------------------------------------------------------------------
# 4. Chargement de tout le corpus + normalisation
# ---------------------------------------------------------------------------

LOADERS = {
    ".pdf": load_pdf,
    ".xlsx": load_excel,
    ".md": load_text,
    ".txt": load_text,
}


def load_documents(data_dir: Path) -> list[Document]:
    """Parcourt data/ et choisit le loader selon l'extension du fichier."""
    if not data_dir.exists():
        raise FileNotFoundError(
            f"Dossier de données introuvable : {data_dir}\n"
            "  -> Générez le corpus avec : python scripts/generate_corpus.py"
        )

    documents: list[Document] = []
    for path in sorted(data_dir.rglob("*")):
        loader = LOADERS.get(path.suffix.lower())
        if loader is None:
            continue
        loaded = loader(path)
        documents.extend(normalize_metadata(loaded, path, data_dir))
    return documents


def normalize_metadata(documents: list[Document], path: Path, data_dir: Path) -> list[Document]:
    """Ajoute des métadonnées communes, quel que soit le format d'origine.

    La catégorie vient du dossier (data/rh/... -> "rh"). Ces métadonnées
    permettront de citer les sources et, plus tard, de filtrer la recherche.
    """
    relative = path.relative_to(data_dir)
    category = relative.parts[0] if len(relative.parts) > 1 else "general"
    for document in documents:
        document.metadata["category"] = category
        document.metadata["path"] = relative.as_posix()
    return documents


# ---------------------------------------------------------------------------
# 5. Découpage (chunking)
# ---------------------------------------------------------------------------


def split_documents(
    documents: list[Document], chunk_size: int = 800, chunk_overlap: int = 100
) -> list[Document]:
    """Découpe les textes longs en morceaux ; laisse les lignes Excel intactes.

    Les métadonnées (source, page, sheet...) sont recopiées dans chaque chunk.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,  # position du chunk dans la page d'origine
    )
    tabular = [doc for doc in documents if doc.metadata.get("doc_type") == "excel"]
    textual = [doc for doc in documents if doc.metadata.get("doc_type") != "excel"]
    return splitter.split_documents(textual) + tabular


# ---------------------------------------------------------------------------
# 6. Pipeline complet d'ingestion
# ---------------------------------------------------------------------------


def build_index(settings: Settings) -> int:
    """Charge, découpe, calcule les embeddings et remplit le vector store."""
    documents = load_documents(settings.data_dir)
    chunks = split_documents(documents, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise ValueError(f"Aucun document exploitable trouvé dans {settings.data_dir}")

    vector_store = create_vector_store(settings, create_embeddings(settings))
    vector_store.reset_collection()  # on repart de zéro à chaque ingestion
    vector_store.add_documents(chunks)  # embeddings calculés ici, via Ollama

    print_summary(documents, chunks)
    return len(chunks)


def print_summary(documents: list[Document], chunks: list[Document]) -> None:
    counts: dict[str, int] = {}
    for chunk in chunks:
        counts[chunk.metadata["source"]] = counts.get(chunk.metadata["source"], 0) + 1
    print(f"{len(documents)} documents chargés -> {len(chunks)} chunks indexés")
    for source, count in sorted(counts.items()):
        print(f"  - {source} : {count} chunks")


if __name__ == "__main__":
    from app.config import OllamaNotReadyError, check_ollama

    current_settings = load_settings()
    try:
        check_ollama(current_settings)
        build_index(current_settings)
    except (OllamaNotReadyError, FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Erreur : {error}")
    print(f"Index enregistré dans {current_settings.chroma_dir}")
