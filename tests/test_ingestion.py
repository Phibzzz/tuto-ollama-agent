"""Tests d'ingestion : PDF -> documents, Excel -> documents, métadonnées."""

from pathlib import Path

from app.ingestion import load_documents, load_excel, load_pdf, split_documents


def test_pdf_gives_one_document_per_page(corpus_dir: Path) -> None:
    documents = load_pdf(corpus_dir / "rh" / "politique-teletravail.pdf")

    assert [doc.metadata["page"] for doc in documents] == [1, 2, 3]
    assert all(doc.metadata["source"] == "politique-teletravail.pdf" for doc in documents)
    assert "2 jours par semaine" in documents[1].page_content


def test_excel_gives_one_document_per_row(corpus_dir: Path) -> None:
    documents = load_excel(corpus_dir / "finance" / "frais-professionnels.xlsx")

    sheets = {doc.metadata["sheet"] for doc in documents}
    assert sheets == {"Barèmes", "Procédure"}
    assert len(documents) == 6 + 4  # 6 lignes de barèmes + 4 étapes de procédure

    meal = next(doc for doc in documents if "Repas professionnel" in doc.page_content)
    # Les en-têtes sont répétés : la ligne se comprend seule.
    assert "Plafond (EUR) : 25" in meal.page_content
    assert meal.metadata["row"] == 2  # ligne 1 = en-têtes


def test_all_documents_have_source_metadata(corpus_dir: Path) -> None:
    documents = load_documents(corpus_dir)

    assert {doc.metadata["source"] for doc in documents} == {
        "politique-teletravail.pdf",
        "conges.pdf",
        "politique-securite.pdf",
        "reglement-interieur.pdf",
        "frais-professionnels.xlsx",
    }
    for doc in documents:
        assert doc.metadata["category"] in {"rh", "securite", "finance", "entreprise"}
        # Un PDF a une page, une ligne Excel a une feuille : jamais les deux.
        assert ("page" in doc.metadata) != ("sheet" in doc.metadata)


def test_split_keeps_excel_rows_intact(corpus_dir: Path) -> None:
    documents = load_documents(corpus_dir)
    chunks = split_documents(documents, chunk_size=200, chunk_overlap=20)

    excel_chunks = [c for c in chunks if c.metadata["doc_type"] == "excel"]
    pdf_chunks = [c for c in chunks if c.metadata["doc_type"] == "pdf"]
    assert len(excel_chunks) == 10  # non découpées
    assert len(pdf_chunks) > 10  # pages découpées en morceaux de 200 caractères
    assert all("page" in c.metadata and "start_index" in c.metadata for c in pdf_chunks)


def test_corrupted_pdf_is_skipped(tmp_path: Path) -> None:
    broken = tmp_path / "casse.pdf"
    broken.write_bytes(b"ceci n'est pas un PDF")

    assert load_pdf(broken) == []


def test_invalid_excel_is_skipped(tmp_path: Path) -> None:
    broken = tmp_path / "casse.xlsx"
    broken.write_text("ceci n'est pas un classeur", encoding="utf-8")

    assert load_excel(broken) == []
