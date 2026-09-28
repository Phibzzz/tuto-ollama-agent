"""Génère le corpus documentaire FICTIF de l'entreprise ACME.

Usage :
    python scripts/generate_corpus.py            # écrit dans data/
    python scripts/generate_corpus.py autre_dir  # écrit ailleurs (utilisé par les tests)

Toutes les données sont inventées et servent uniquement à la démonstration.
Les PDF sont produits avec fpdf2 (polices standard Latin-1 : on écrit "EUR"
plutôt que le symbole euro). Le fichier Excel est produit avec openpyxl.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fpdf import FPDF
from openpyxl import Workbook

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Chaque PDF = une liste de pages ; chaque page = (titre de section, paragraphes).
Page = tuple[str, list[str]]

PDF_DOCUMENTS: dict[str, tuple[str, list[Page]]] = {
    "rh/politique-teletravail.pdf": (
        "Politique de télétravail",
        [
            (
                "1. Principes généraux",
                [
                    "La présente politique définit les conditions dans lesquelles les "
                    "salariés d'ACME peuvent exercer leur activité en télétravail.",
                    "Le télétravail repose sur le volontariat du salarié et l'accord de "
                    "son manager. Il peut être suspendu en cas de nécessité de service.",
                    "Le télétravail est ouvert aux salariés en CDI et en CDD ayant "
                    "terminé leur période d'essai. Les alternants et stagiaires peuvent "
                    "télétravailler 1 jour par semaine avec l'accord de leur tuteur.",
                ],
            ),
            (
                "2. Organisation du télétravail",
                [
                    "Les salariés éligibles peuvent télétravailler jusqu'à 2 jours par "
                    "semaine au maximum. Les jours non utilisés ne sont pas reportables "
                    "d'une semaine sur l'autre.",
                    "Les jours de télétravail sont fixes et définis avec le manager. "
                    "Le mardi est un jour de présence obligatoire sur site pour toutes "
                    "les équipes.",
                    "Une indemnité forfaitaire de télétravail de 10 EUR par mois est "
                    "versée aux salariés qui télétravaillent au moins 1 jour par semaine.",
                ],
            ),
            (
                "3. Équipement et sécurité",
                [
                    "ACME fournit un ordinateur portable et un casque. Le salarié doit "
                    "disposer d'une connexion internet personnelle stable.",
                    "En télétravail, le salarié doit respecter la politique de sécurité "
                    "informatique d'ACME, en particulier l'utilisation obligatoire du VPN "
                    "et le verrouillage de l'écran en cas d'absence.",
                    "Tout incident (perte, vol, suspicion de piratage) doit être signalé "
                    "selon la procédure décrite dans la politique de sécurité.",
                ],
            ),
        ],
    ),
    "rh/conges.pdf": (
        "Politique de congés",
        [
            (
                "1. Droits à congés",
                [
                    "Chaque salarié à temps plein bénéficie de 25 jours ouvrés de congés "
                    "payés par an, acquis à raison de 2,08 jours par mois travaillé.",
                    "En complément, les salariés au forfait jours bénéficient de 10 jours "
                    "de RTT par an.",
                    "La période de référence pour l'acquisition des congés va du 1er juin "
                    "au 31 mai de l'année suivante.",
                ],
            ),
            (
                "2. Demande et report",
                [
                    "Toute demande de congé de plus de 5 jours consécutifs doit être "
                    "déposée dans l'outil RH au moins 1 mois à l'avance.",
                    "Les congés non pris au 31 mai peuvent être reportés, dans la limite "
                    "de 5 jours, jusqu'au 31 décembre suivant.",
                    "Les congés exceptionnels (mariage, naissance, décès) sont accordés "
                    "conformément à la convention collective applicable.",
                ],
            ),
        ],
    ),
    "securite/politique-securite.pdf": (
        "Politique de sécurité informatique",
        [
            (
                "1. Mots de passe et authentification",
                [
                    "Les mots de passe doivent comporter au moins 12 caractères et "
                    "mélanger lettres, chiffres et caractères spéciaux.",
                    "L'authentification multifacteur (MFA) est obligatoire pour la "
                    "messagerie et toutes les applications de l'entreprise.",
                    "Il est interdit de partager son mot de passe, y compris avec un "
                    "collègue ou un manager.",
                ],
            ),
            (
                "2. Travail hors des locaux",
                [
                    "En dehors des locaux ACME (télétravail, déplacement), la connexion "
                    "au VPN de l'entreprise est obligatoire pour accéder aux ressources "
                    "internes.",
                    "L'utilisation d'un Wi-Fi public (gare, hôtel, café) sans VPN est "
                    "interdite.",
                    "L'écran doit être verrouillé dès que le poste est laissé sans "
                    "surveillance. Les documents confidentiels ne doivent pas être "
                    "imprimés au domicile.",
                ],
            ),
            (
                "3. Signalement des incidents",
                [
                    "Tout incident de sécurité (perte ou vol de matériel, courriel "
                    "suspect, suspicion de piratage) doit être signalé dans un délai de "
                    "24 heures à l'adresse securite@acme.example.",
                    "Les clés USB personnelles sont interdites sur les postes de travail.",
                ],
            ),
        ],
    ),
    "entreprise/reglement-interieur.pdf": (
        "Règlement intérieur",
        [
            (
                "1. Horaires et accès",
                [
                    "Les locaux d'ACME sont ouverts de 7h30 à 20h00 du lundi au vendredi.",
                    "La plage horaire de présence commune est fixée de 10h00 à 16h00.",
                    "Le badge d'accès est personnel et doit être porté de manière visible.",
                ],
            ),
            (
                "2. Achats et comportement",
                [
                    "Tout achat supérieur à 1 000 EUR HT nécessite la présentation de "
                    "3 devis et la validation du service Achats avant commande.",
                    "Les cadeaux de fournisseurs d'une valeur supérieure à 50 EUR doivent "
                    "être déclarés au service juridique.",
                    "Les salariés s'engagent à adopter un comportement respectueux envers "
                    "leurs collègues, clients et partenaires.",
                ],
            ),
        ],
    ),
}

# Feuilles Excel : nom de feuille -> (en-têtes, lignes)
EXCEL_SHEETS: dict[str, tuple[list[str], list[list[object]]]] = {
    "Barèmes": (
        ["Catégorie", "Plafond (EUR)", "Unité", "Justificatif", "Commentaire"],
        [
            ["Repas professionnel", 25, "par repas", "Facture nominative",
             "Invitation d'un client : plafond de 50 EUR par personne"],
            ["Hôtel Paris", 150, "par nuit", "Facture de l'hôtel", "Petit-déjeuner inclus"],
            ["Hôtel province", 110, "par nuit", "Facture de l'hôtel", "Petit-déjeuner inclus"],
            ["Indemnités kilométriques", 0.35, "par km", "Relevé de trajet",
             "Uniquement si aucun transport en commun n'est adapté"],
            ["Train", None, "par trajet", "Billet", "2nde classe obligatoire"],
            ["Taxi", 40, "par trajet", "Reçu", "Uniquement après 22h ou avec bagages lourds"],
        ],
    ),
    "Procédure": (
        ["Étape", "Action", "Délai"],
        [
            [1, "Conserver tous les justificatifs originaux", "Pendant le déplacement"],
            [2, "Saisir la note de frais dans l'outil Finance", "Sous 3 mois maximum"],
            [3, "Validation par le manager", "Sous 10 jours"],
            [4, "Remboursement sur le salaire", "Mois suivant la validation"],
        ],
    ),
}


def write_pdf(path: Path, title: str, pages: list[Page]) -> None:
    """Écrit un PDF simple : une section par page."""
    pdf = FPDF()
    for section_title, paragraphs in pages:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, f"ACME - {title}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "I", 9)
        pdf.cell(0, 6, "Document fictif - usage pédagogique uniquement", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, section_title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        for paragraph in paragraphs:
            pdf.multi_cell(0, 6, paragraph, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))


def write_excel(path: Path) -> None:
    """Écrit le classeur des frais professionnels (une feuille par tableau)."""
    workbook = Workbook()
    workbook.remove(workbook.active)  # supprime la feuille vide par défaut
    for sheet_name, (headers, rows) in EXCEL_SHEETS.items():
        sheet = workbook.create_sheet(sheet_name)
        sheet.append(headers)
        for row in rows:
            sheet.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def generate_corpus(data_dir: Path = DEFAULT_DATA_DIR) -> list[Path]:
    """Génère tous les documents et retourne la liste des fichiers créés."""
    created: list[Path] = []
    for relative_path, (title, pages) in PDF_DOCUMENTS.items():
        path = data_dir / relative_path
        write_pdf(path, title, pages)
        created.append(path)
    excel_path = data_dir / "finance" / "frais-professionnels.xlsx"
    write_excel(excel_path)
    created.append(excel_path)
    return created


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA_DIR
    for created_file in generate_corpus(target):
        print(f"créé : {created_file}")
