# Instructions de développement

Ce document permet de **reconstruire le projet from scratch**, étape par étape, sans
utiliser le code final comme raccourci. Chaque étape suit la même structure :
*Objectif, Fichiers concernés, Action, Code à écrire, Commande à exécuter, Résultat
attendu, Point pédagogique*.

Conventions :

- Les commandes sont données pour **Windows PowerShell** ; l'équivalent macOS/Linux est
  indiqué quand il diffère.
- Toutes les commandes s'exécutent **à la racine du projet**, avec l'environnement
  virtuel activé.
- Les petits essais se font dans un fichier jetable `playground.py` (à supprimer à la fin).
- Le code donné ici est **identique** au code final du dépôt.

Progression :

```text
Étape 1  Ollama → LLM                                   (étapes 4-5)
Étape 2  Ollama → LangChain → LLM                       (étape 17)
Étape 3  Documents → Loader → Documents LangChain       (étapes 7-11)
Étape 4  Documents → Chunking → Embeddings → Vector store (étapes 12-14)
Étape 5  Question → Retriever → Documents pertinents    (étapes 15-16)
Étape 6  Question → Agent → Tool → Retriever            (étapes 18-20)
Étape 7  ... → LLM → Réponse + sources                  (étapes 21-22)
Étape 8  Tout le workflow → Langfuse                    (étapes 23-24)
```

---

## 0. Prérequis

### Objectif

Vérifier que la machine dispose des outils nécessaires.

### Fichiers concernés

Aucun.

### Action

Vérifier Python (3.11 ou plus), pip et git (facultatif).

### Code à écrire

Aucun.

### Commande à exécuter

```powershell
python --version
python -m pip --version
git --version
```

### Résultat attendu

```text
Python 3.13.10      (toute version >= 3.11 convient)
pip 25.x ...
git version 2.x ...
```

### Point pédagogique

Le projet est testé avec Python 3.13.10. `pandas` 3 exige Python 3.11 au minimum :
c'est la contrainte la plus forte de la stack.

---

## 1. Créer le projet Python

### Objectif

Créer l'arborescence du projet et les fichiers de configuration de base.

### Fichiers concernés

`app/`, `scripts/`, `tests/`, `examples/`, `data/`, `pyproject.toml`, `.gitignore`, `app/__init__.py`

### Action

Créer les dossiers, puis `pyproject.toml` (métadonnées + configuration pytest),
`.gitignore` et un `app/__init__.py`.

### Code à écrire

`app/__init__.py` :

```python
"""ACME Company Documentation Agent - projet pédagogique."""
```

`pyproject.toml` :

```toml
[project]
name = "company-doc-agent"
version = "0.1.0"
description = "Tutoriel : agent documentaire d'entreprise avec LangChain, Ollama, Chroma et Langfuse"
readme = "README.md"
requires-python = ">=3.11"
# Versions exactes : voir requirements.txt

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
markers = [
    "ollama: test d'intégration qui appelle le vrai modèle Ollama (lancer avec `pytest -m ollama`)",
]
addopts = "-m 'not ollama'"
filterwarnings = [
    "ignore::DeprecationWarning:chromadb.*",
]
```

`.gitignore` :

```text
# Secrets : ne jamais versionner
.env

# Environnement Python
.venv/
__pycache__/
*.pyc
.pytest_cache/

# Index vectoriel (régénéré par : python -m app.ingestion)
.chroma/

# IDE / OS
.vscode/
.idea/
Thumbs.db
.DS_Store
```

### Commande à exécuter

```powershell
mkdir company-doc-agent; cd company-doc-agent
mkdir app, scripts, tests, examples, data
# macOS/Linux : mkdir -p company-doc-agent/{app,scripts,tests,examples,data} && cd company-doc-agent
```

### Résultat attendu

```text
company-doc-agent/
├── app/__init__.py
├── scripts/  tests/  examples/  data/
├── pyproject.toml
└── .gitignore
```

### Point pédagogique

`.env` (secrets) et `.chroma/` (index régénérable) sont exclus du versionnement **dès le
départ** : on ne rattrape pas un secret poussé par erreur. L'option `pythonpath = ["."]`
permet à pytest d'importer le paquet `app`.

---

## 2. Créer l'environnement virtuel

### Objectif

Isoler les dépendances du projet.

### Fichiers concernés

`.venv/`

### Action

Créer et activer un environnement virtuel avec le module standard `venv`.

### Code à écrire

Aucun.

### Commande à exécuter

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
# macOS/Linux : python3 -m venv .venv && source .venv/bin/activate
```

### Résultat attendu

L'invite de commande est préfixée par `(.venv)` ; `python -c "import sys; print(sys.prefix)"`
affiche un chemin se terminant par `.venv`.

### Point pédagogique

Épingler des versions n'a de sens que dans un environnement isolé : c'est la base de la
reproductibilité du tutoriel.

---

## 3. Installer les dépendances

### Objectif

Installer la stack avec des versions épinglées.

### Fichiers concernés

`requirements.txt`

### Action

Créer `requirements.txt`, puis l'installer.

### Code à écrire

```text
# Versions vérifiées le 2026-09-27 (Python 3.13.10, Ollama 0.34.0).
# Orchestration LLM / agent
langchain==1.4.2
langchain-core==1.6.5
langchain-ollama==1.1.0
langchain-text-splitters==1.1.2
# Vector store local
langchain-chroma==1.1.0
chromadb==1.5.9
# Formats documentaires
pypdf==6.19.0
pandas==3.0.6
openpyxl==3.1.5
# Génération du corpus fictif (PDF)
fpdf2==2.8.8
# Monitoring
langfuse==4.15.6
# Configuration & tests
python-dotenv==1.2.3
pytest==9.1.1
```

### Commande à exécuter

```powershell
python -m pip install -r requirements.txt
python -c "import langchain, langchain_ollama, langchain_chroma, langfuse, pypdf, pandas; print('OK', langchain.__version__)"
```

### Résultat attendu

```text
OK 1.4.2
```

### Point pédagogique

Chaque intégration LangChain vit dans **son propre paquet** (`langchain-ollama`,
`langchain-chroma`...). On n'installe **pas** `langchain-community`, en fin de vie
(il émet un `DeprecationWarning` à l'import). `langgraph` est installé automatiquement
comme dépendance de `langchain` : `create_agent` s'appuie sur son moteur d'exécution.

---

## 4. Installer et vérifier Ollama

### Objectif

Disposer d'un serveur de modèles local.

### Fichiers concernés

Aucun.

### Action

Installer Ollama depuis https://ollama.com/download puis lancer l'application
(ou `ollama serve` dans un terminal dédié).

### Code à écrire

Aucun.

### Commande à exécuter

```powershell
ollama --version
ollama list
curl http://localhost:11434/api/tags
```

### Résultat attendu

```text
ollama version is 0.34.0
NAME    ID    SIZE    MODIFIED          (liste éventuellement vide)
{"models":[...]}
```

### Point pédagogique

Ollama expose une **API HTTP** locale (port 11434). Toutes les bibliothèques (LangChain,
client `ollama`, curl) ne font que lui envoyer des requêtes HTTP.

---

## 5. Télécharger le modèle Ollama

### Objectif

Télécharger le LLM de génération et le modèle d'embeddings, puis faire le **premier
appel** au LLM (progression, étape 1 : Ollama → LLM).

### Fichiers concernés

Aucun.

### Action

Télécharger deux modèles **différents** : un pour générer, un pour vectoriser.

### Code à écrire

Aucun.

### Commande à exécuter

```powershell
ollama pull llama3.1:8b
ollama pull nomic-embed-text
ollama run llama3.1:8b "Explique en une phrase ce qu'est un agent LLM."
```

### Résultat attendu

Une phrase en français générée localement. `ollama list` affiche `llama3.1:8b` et
`nomic-embed-text:latest`.

### Point pédagogique

`llama3.1:8b` est choisi parce qu'il sait faire du **tool calling** (voir
https://ollama.com/search?c=tools), pas seulement pour sa taille. Sur une machine plus
modeste : `llama3.2:3b` (moins fiable) ; plus puissante : `qwen3:8b` ou `gpt-oss:20b`.

---

## 6. Créer le fichier .env

### Objectif

Centraliser la configuration, sans secret dans le code.

### Fichiers concernés

`.env.example`, `.env`, `app/config.py`

### Action

1. Créer `.env.example` (versionné, sans secret) puis le copier en `.env` (non versionné).
2. Créer `app/config.py` : un objet `Settings` immuable construit depuis l'environnement.

### Code à écrire

`.env.example` :

```ini
# Copier ce fichier en .env puis compléter. Ne jamais versionner .env.

# --- Ollama (LLM local + embeddings) ---
OLLAMA_BASE_URL=http://localhost:11434
# Modèle de génération : doit supporter le tool calling (https://ollama.com/search?c=tools)
OLLAMA_MODEL=llama3.1:8b
# Modèle d'embeddings : différent du LLM, sert uniquement à vectoriser les textes
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# --- Corpus et index ---
DATA_DIR=data
CHROMA_DIR=.chroma
CHROMA_COLLECTION=acme_docs
CHUNK_SIZE=800
CHUNK_OVERLAP=100
# Nombre de passages renvoyés par l'outil de recherche
TOP_K=4
# Score de pertinence minimal (0 à 1) pour qu'un passage soit transmis au LLM
MIN_SCORE=0.55

# --- Langfuse (optionnel : sans clés, le traçage est désactivé) ---
# Clés : Langfuse > Project > Settings > API Keys
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
# Région EU : https://cloud.langfuse.com | US : https://us.cloud.langfuse.com | self-hosted : http://localhost:3000
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

`app/config.py` (première version ; `check_ollama` sera ajouté à l'étape 22) :

```python
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
```

### Commande à exécuter

```powershell
Copy-Item .env.example .env        # macOS/Linux : cp .env.example .env
python -c "from app.config import load_settings; print(load_settings())"
```

### Résultat attendu

```text
Settings(ollama_base_url='http://localhost:11434', ollama_model='llama3.1:8b', ...)
```

### Point pédagogique

Les autres modules reçoivent un `Settings` en paramètre au lieu de lire `os.environ`
eux-mêmes : le code est plus facile à tester (on peut passer une configuration de test).
`load_dotenv()` copie aussi les variables `LANGFUSE_*` dans l'environnement, où le SDK
Langfuse les lira directement.

---

## 7. Créer les premiers documents PDF

### Objectif

Disposer d'un corpus **fictif**, petit et reproductible.

### Fichiers concernés

`scripts/generate_corpus.py`, `data/**`

### Action

Écrire un script qui génère les PDF (avec `fpdf2`) et, à l'étape suivante, le fichier
Excel (avec `openpyxl`). Le script complet est donné ici ; l'étape 8 détaille la partie Excel.

### Code à écrire

`scripts/generate_corpus.py` :

```python
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
```

### Commande à exécuter

```powershell
python scripts/generate_corpus.py
```

### Résultat attendu

```text
créé : ...\data\rh\politique-teletravail.pdf
créé : ...\data\rh\conges.pdf
créé : ...\data\securite\politique-securite.pdf
créé : ...\data\entreprise\reglement-interieur.pdf
créé : ...\data\finance\frais-professionnels.xlsx
```

Ouvrez un PDF : une section par page, avec la mention « Document fictif ».

### Point pédagogique

Générer le corpus par script le rend **reproductible** et **testable** (les tests le
régénèrent dans un dossier temporaire). Le corpus ne contient volontairement **aucune
politique « véhicules de fonction »**, pour tester le cas « information absente ».
Les polices standard de fpdf2 sont en Latin-1 : on écrit « EUR » plutôt que « € ».

---

## 8. Créer le fichier Excel de démonstration

### Objectif

Disposer d'un document **tabulaire**, différent par nature d'un PDF.

### Fichiers concernés

`scripts/generate_corpus.py` (fonction `write_excel` et constante `EXCEL_SHEETS`), `data/finance/frais-professionnels.xlsx`

### Action

Relire la partie Excel du script : deux feuilles, « Barèmes » et « Procédure », avec
une ligne d'en-têtes puis des lignes de données.

### Code à écrire

Déjà écrit à l'étape 7 :

```python
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
```

### Commande à exécuter

```powershell
python -c "import pandas as pd; print(pd.read_excel('data/finance/frais-professionnels.xlsx', sheet_name=None))"
```

### Résultat attendu

Un dictionnaire `{'Barèmes': DataFrame(6 lignes), 'Procédure': DataFrame(4 lignes)}`.

### Point pédagogique

Dans un tableau, **une valeur n'a de sens qu'avec son en-tête de colonne** : « 25 » ne
veut rien dire, « Plafond (EUR) : 25 » oui. Cela guidera la manière de l'indexer (étape 10).

---

## 9. Implémenter le chargement des PDF

### Objectif

Transformer un PDF en `Document` LangChain (progression, étape 3 : Documents → Loader → Documents LangChain).

### Fichiers concernés

`app/ingestion.py`

### Action

Créer `app/ingestion.py` avec l'en-tête et la fonction `load_pdf` : un `Document` par page,
avec les métadonnées `source`, `page`, `doc_type`.

### Code à écrire

En-tête du fichier. **La ligne `from app.retrieval import ...` ne sera valide qu'à
l'étape 13-14 : commentez-la d'ici là.**

```python
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
```

Puis :

```python
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
```

### Commande à exécuter

```powershell
python -c "from pathlib import Path; from app.ingestion import load_pdf; docs = load_pdf(Path('data/rh/politique-teletravail.pdf')); print(len(docs)); print(docs[1].metadata); print(docs[1].page_content[:200])"
```

### Résultat attendu

```text
3
{'source': 'politique-teletravail.pdf', 'page': 2, 'doc_type': 'pdf'}
ACME - Politique de télétravail
Document fictif - usage pédagogique uniquement
2. Organisation du télétravail
Les salariés éligibles peuvent télétravailler jusqu'à 2 jours par semaine ...
```

### Point pédagogique

Un `Document` LangChain = `page_content` (le texte) + `metadata` (d'où il vient). Les
métadonnées sont ce qui permettra de **citer les sources**. On numérote les pages à
partir de 1, comme un lecteur PDF. Un PDF illisible est signalé et ignoré, sans
interrompre l'ingestion.

---

## 10. Implémenter le chargement Excel

### Objectif

Transformer un tableau Excel en `Document`s exploitables par une recherche textuelle.

### Fichiers concernés

`app/ingestion.py`

### Action

Lire toutes les feuilles avec `pandas.read_excel(sheet_name=None)`, puis transformer
**chaque ligne** en un petit texte autonome qui répète les en-têtes.

### Code à écrire

```python
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
```

### Commande à exécuter

```powershell
python -c "from pathlib import Path; from app.ingestion import load_excel; docs = load_excel(Path('data/finance/frais-professionnels.xlsx')); print(len(docs)); print(docs[0].page_content); print(docs[0].metadata)"
```

### Résultat attendu

```text
10
Feuille « Barèmes » - Catégorie : Repas professionnel ; Plafond (EUR) : 25 ; Unité : par repas ; Justificatif : Facture nominative ; Commentaire : Invitation d'un client : plafond de 50 EUR par personne
{'source': 'frais-professionnels.xlsx', 'sheet': 'Barèmes', 'row': 2, 'doc_type': 'excel'}
```

### Point pédagogique

```text
PDF   → texte semi-structuré → 1 Document par page  → découpé ensuite
Excel → données tabulaires   → 1 Document par ligne → PAS découpé
```

Si l'on concaténait tout le classeur en un seul texte découpé tous les 800 caractères,
un montant pourrait se retrouver séparé de sa catégorie. La ligne Excel `row` est la
vraie ligne du fichier (la ligne 1 contient les en-têtes).

---

## 11. Normaliser les documents

### Objectif

Charger tout le corpus avec des métadonnées **homogènes**, quel que soit le format.

### Fichiers concernés

`app/ingestion.py`

### Action

Ajouter un loader texte/Markdown optionnel, un dictionnaire extension → loader, la
fonction `load_documents` qui parcourt `data/`, et `normalize_metadata` qui ajoute la
catégorie (nom du sous-dossier) et le chemin relatif.

### Code à écrire

```python
def load_text(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8")
    return [Document(page_content=text, metadata={"source": path.name, "doc_type": "text"})]


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
```

### Commande à exécuter

```powershell
python -c "from app.config import load_settings; from app.ingestion import load_documents; docs = load_documents(load_settings().data_dir); print(len(docs)); print({d.metadata['category'] for d in docs})"
```

### Résultat attendu

```text
20
{'rh', 'securite', 'finance', 'entreprise'}
```

### Point pédagogique

La **normalisation** est ce qui permet au reste du pipeline d'ignorer le format
d'origine : l'outil de recherche manipulera des `Document`s tous équivalents. La
catégorie servira plus tard à filtrer (ex. uniquement les documents RH).

---

## 12. Découper les documents

### Objectif

Produire des morceaux (*chunks*) de taille adaptée à la recherche.

### Fichiers concernés

`app/ingestion.py`

### Action

Découper **uniquement** les documents textuels avec `RecursiveCharacterTextSplitter` ;
laisser les lignes Excel intactes.

### Code à écrire

```python
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
```

### Commande à exécuter

```powershell
python -c "from app.config import load_settings; from app.ingestion import load_documents, split_documents; docs = load_documents(load_settings().data_dir); print(len(split_documents(docs)), len(split_documents(docs, 200, 20)))"
```

### Résultat attendu

```text
20 45
```

(avec 800 caractères, chaque page tient dans un chunk ; avec 200, les pages sont découpées.)

### Point pédagogique

Un passage court et ciblé est mieux retrouvé qu'une page qui parle de tout. Le
*splitter* coupe d'abord sur les paragraphes, puis les lignes, puis les mots, et
**recopie les métadonnées** dans chaque chunk : la page d'origine reste connue.
`add_start_index=True` ajoute la position du chunk dans la page.

---

## 13. Configurer les embeddings

### Objectif

Transformer du texte en vecteurs avec un modèle local (progression, étape 4).

### Fichiers concernés

`app/retrieval.py`

### Action

Créer `app/retrieval.py` avec `create_embeddings`. Pour `nomic-embed-text`, ajouter les
**préfixes de tâche** exigés par le modèle (`search_document:` / `search_query:`).

### Code à écrire

```python
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
```

### Commande à exécuter

```powershell
python -c "from app.config import load_settings; from app.retrieval import create_embeddings; v = create_embeddings(load_settings()).embed_query('plafond repas'); print(len(v), v[:3])"
```

### Résultat attendu

```text
768 [0.0123, -0.0456, ...]        (valeurs indicatives)
```

### Point pédagogique

> Le modèle de génération et le modèle d'embeddings sont deux composants différents.
> LLM → génère la réponse. Modèle d'embeddings → représente documents et questions sous forme vectorielle.

Un vecteur de 768 nombres ne « contient » pas le texte : il en capture le sens. Deux
textes proches ont des vecteurs proches. Changer de modèle d'embeddings impose de
réindexer. Sans les préfixes, sur notre évaluation, une question sur les devis ne
retrouvait plus le règlement intérieur.

---

## 14. Créer le vector store

### Objectif

Stocker les vecteurs de tous les chunks dans une base locale persistée.

### Fichiers concernés

`app/retrieval.py`, `app/ingestion.py`

### Action

1. Ajouter `create_vector_store` dans `retrieval.py` (Chroma, dossier `.chroma/`, distance cosinus).
2. Décommenter l'import `from app.retrieval import ...` dans `ingestion.py`.
3. Ajouter `build_index`, `print_summary` et le point d'entrée `__main__` dans `ingestion.py`.

### Code à écrire

`app/retrieval.py` :

```python
def create_vector_store(settings: Settings, embeddings: Embeddings) -> Chroma:
    """Vector store Chroma persisté sur disque (dossier .chroma/), sans serveur."""
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=embeddings,
        persist_directory=str(settings.chroma_dir),
        # distance cosinus -> scores de pertinence faciles à lire (1 = identique)
        collection_configuration={"hnsw": {"space": "cosine"}},
    )
```

`app/ingestion.py` — fichier complet à ce stade :

```python
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
```

### Commande à exécuter

```powershell
python -m app.ingestion
```

### Résultat attendu

```text
20 documents chargés -> 20 chunks indexés
  - conges.pdf : 2 chunks
  - frais-professionnels.xlsx : 10 chunks
  - politique-securite.pdf : 3 chunks
  - politique-teletravail.pdf : 3 chunks
  - reglement-interieur.pdf : 2 chunks
Index enregistré dans ...\.chroma
```

(`check_ollama` est ajouté à l'étape 22 : d'ici là, retirez temporairement les deux lignes
qui l'utilisent dans le bloc `__main__`, ou faites l'étape 22 dès maintenant.)

### Point pédagogique

C'est ici que l'**ingestion** se termine : elle tourne une fois, hors ligne. Chroma est
choisi car il s'installe avec pip, persiste dans un dossier et ne demande aucun serveur.
`reset_collection()` repart de zéro à chaque ingestion (pas d'indexation incrémentale :
c'est une limite assumée).

---

## 15. Créer le retriever

### Objectif

Ouvrir l'index existant et rechercher les passages proches d'une question
(progression, étape 5 : Question → Retriever → Documents pertinents).

### Fichiers concernés

`app/retrieval.py`

### Action

Ajouter : l'erreur `IndexNotFoundError`, `load_vector_store` (message clair si l'index
n'existe pas), `search_documents` (avec seuil de pertinence) et `format_source`.

### Code à écrire

```python
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
```

Fichier complet `app/retrieval.py` à ce stade :

```python
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
```

### Commande à exécuter

```powershell
python -c "from app.config import load_settings; from app.retrieval import *; s = load_settings(); vs = load_vector_store(s); [print(round(sc, 3), format_source(d)) for d, sc in search_documents(vs, 'plafond repas professionnel')]"
```

### Résultat attendu

```text
0.794 frais-professionnels.xlsx, feuille « Barèmes », ligne 2
...
```

### Point pédagogique

La recherche vectorielle compare le vecteur de la question à ceux des chunks (distance
cosinus : score de 0 à 1). `format_source` n'affiche une page ou une feuille **que si elle
existe** dans les métadonnées : on n'invente jamais de localisation.

---

## 16. Tester la recherche documentaire

### Objectif

Valider le retrieval **indépendamment** de l'agent et du LLM.

### Fichiers concernés

`scripts/search_demo.py`

### Action

Écrire un petit script qui affiche les passages trouvés, leur source et leur score.

### Code à écrire

```python
"""Étape 5 du tutoriel : tester la recherche SANS agent et SANS LLM.

    python scripts/search_demo.py "plafond repas professionnel"

Affiche les passages retrouvés, leur source et leur score de pertinence.
Si la recherche ne trouve pas les bons passages, l'agent ne pourra pas
bien répondre : on vérifie donc le retrieval séparément.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_settings  # noqa: E402
from app.retrieval import format_source, load_vector_store, search_documents  # noqa: E402


def main() -> None:
    query = " ".join(sys.argv[1:]) or "Quelle est la politique de télétravail ?"
    settings = load_settings()
    vector_store = load_vector_store(settings)

    print(f"Requête : {query}\n")
    for document, score in search_documents(vector_store, query, k=settings.top_k):
        print(f"[{score:.3f}] {format_source(document)}")
        print(f"        {document.page_content[:150].strip()!r}\n")


if __name__ == "__main__":
    main()
```

### Commande à exécuter

```powershell
python scripts/search_demo.py "plafond repas professionnel"
python scripts/search_demo.py "combien de jours de télétravail"
python scripts/search_demo.py "recette de la tarte aux pommes"
```

### Résultat attendu

Les deux premières requêtes placent en tête `frais-professionnels.xlsx` (feuille
« Barèmes ») puis `politique-teletravail.pdf`. La troisième renvoie quand même des
passages, avec un score à peine plus faible (≈ 0.70 contre ≈ 0.79).

### Point pédagogique

**Si le bon passage n'est pas trouvé ici, aucun prompt ne sauvera la réponse.** Et un
seuil de score ne suffit pas à détecter une question hors sujet avec un petit modèle
d'embeddings : c'est au LLM, guidé par ses instructions, de juger la pertinence.

---

## 17. Connecter Ollama à LangChain

### Objectif

Créer le premier appel LangChain vers le modèle local (progression, étape 2 : Ollama → LangChain → LLM).

### Fichiers concernés

`app/agent.py`, `playground.py`

### Action

Créer `app/agent.py` avec la fonction `create_llm`, puis l'appeler depuis `playground.py`.

### Code à écrire

`app/agent.py` (début ; l'en-tête complet est donné à l'étape 21) :

```python
from langchain_ollama import ChatOllama

from app.config import Settings


def create_llm(settings: Settings) -> ChatOllama:
    """Le LLM local. temperature=0 : réponses plus stables, utile en démo."""
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )
```

`playground.py` :

```python
from app.agent import create_llm
from app.config import load_settings

llm = create_llm(load_settings())
response = llm.invoke("Explique en une phrase ce qu'est un embedding.")
print(type(response).__name__)
print(response.content)
print(response.usage_metadata)
```

### Commande à exécuter

```powershell
python playground.py
```

### Résultat attendu

```text
AIMessage
Un embedding est une représentation vectorielle ...
{'input_tokens': ..., 'output_tokens': ..., 'total_tokens': ...}
```

### Point pédagogique

LangChain **orchestre** l'appel, mais le modèle est exécuté **localement par Ollama**.
`ChatOllama` remplace l'ancien `langchain_community.llms.Ollama` et supporte le tool
calling. `temperature=0` rend les réponses plus stables pour une démonstration.

---

## 18. Créer le premier agent

### Objectif

Comprendre `create_agent` avant d'y brancher un outil.

### Fichiers concernés

`app/agent.py`, `playground.py`

### Action

1. Ajouter le *system prompt* dans `app/agent.py`.
2. Créer un agent **sans outil** dans `playground.py` et lui poser une question sur ACME.

### Code à écrire

`app/agent.py` :

```python
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
```

`playground.py` :

```python
from langchain.agents import create_agent

from app.agent import SYSTEM_PROMPT, create_llm
from app.config import load_settings

agent = create_agent(model=create_llm(load_settings()), tools=[], system_prompt=SYSTEM_PROMPT)
result = agent.invoke({"messages": [{"role": "user", "content": "Combien de jours de télétravail chez ACME ?"}]})
for message in result["messages"]:
    print(type(message).__name__, ":", message.content[:200])
```

### Commande à exécuter

```powershell
python playground.py
```

### Résultat attendu

```text
HumanMessage : Combien de jours de télétravail chez ACME ?
AIMessage : Je vais chercher les informations dans la documentation ACME.
Après avoir consulté les documents, je n'ai trouvé aucune information ...
```

(Réponse observée avec `llama3.1:8b` ; elle peut varier.)

### Point pédagogique

Un agent = **modèle + instructions + outils + boucle**. Sans outil, le LLM n'a accès à
aucun document : il refuse ou il invente. Remarquez qu'il **prétend** avoir « consulté
les documents » alors qu'aucun outil n'existe : seule la trace des messages (ou Langfuse)
permet de vérifier ce qui s'est réellement passé. Le résultat de `invoke` est l'**historique des
messages** : c'est l'« état » de l'agent. `create_agent` (LangChain v1) remplace
`initialize_agent` / `AgentExecutor` des anciens tutoriels.

---

## 19. Créer l'outil search_company_documents

### Objectif

Exposer la recherche documentaire comme un outil appelable par le LLM.

### Fichiers concernés

`app/tools.py`, `playground.py`

### Action

Créer une fonction « fabrique » qui reçoit le vector store et retourne un outil décoré
par `@tool`, avec `response_format="content_and_artifact"`.

### Code à écrire

`app/tools.py` :

```python
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
```

`playground.py` — appeler l'outil **sans LLM**, exactement comme le fera l'agent :

```python
from app.config import load_settings
from app.retrieval import load_vector_store
from app.tools import make_search_tool

tool = make_search_tool(load_vector_store(load_settings()), k=2)
print("Nom :", tool.name)
print("Description vue par le LLM :", tool.description)
print("Arguments :", tool.args)

message = tool.invoke({"type": "tool_call", "id": "1", "name": tool.name, "args": {"query": "plafond repas"}})
print(message.content)
print([doc.metadata for doc in message.artifact])
```

### Commande à exécuter

```powershell
python playground.py
```

### Résultat attendu

```text
Nom : search_company_documents
Description vue par le LLM : Recherche dans la documentation interne ...
Arguments : {'query': {'title': 'Query', 'type': 'string'}}
--- Passage 1 ---
Source : frais-professionnels.xlsx, feuille « Barèmes », ligne 2
Contenu : Feuille « Barèmes » - Catégorie : Repas professionnel ; Plafond (EUR) : 25 ; ...
[{'source': 'frais-professionnels.xlsx', 'sheet': 'Barèmes', 'row': 2, ...}, ...]
```

### Point pédagogique

Le LLM ne voit **jamais le code** de l'outil : seulement son **nom**, sa **docstring** et
ses **paramètres**. La docstring est donc un prompt. `content_and_artifact` sépare :
`content` (texte envoyé au LLM) et `artifact` (objets `Document` gardés pour notre code,
non envoyés au LLM).

```text
Agent → Tool → Retriever → Vector store → Documents
```

---

## 20. Connecter l'outil à l'agent

### Objectif

Obtenir un agent qui décide seul d'appeler la recherche (progression, étape 6).

### Fichiers concernés

`app/agent.py`, `playground.py`

### Action

Ajouter `create_documentation_agent` dans `app/agent.py`, puis observer les messages
échangés.

### Code à écrire

`app/agent.py` (ajouter aussi les imports `from langchain.agents import create_agent`,
`from langchain_chroma import Chroma` et `from app.tools import make_search_tool`) :

```python
def create_documentation_agent(settings: Settings, vector_store: Chroma):
    """Assemble le modèle, l'outil de recherche et les instructions."""
    search_tool = make_search_tool(vector_store, k=settings.top_k, min_score=settings.min_score)
    return create_agent(
        model=create_llm(settings),
        tools=[search_tool],
        system_prompt=SYSTEM_PROMPT,
    )
```

`playground.py` :

```python
from app.agent import create_documentation_agent
from app.config import load_settings
from app.retrieval import load_vector_store

settings = load_settings()
agent = create_documentation_agent(settings, load_vector_store(settings))
result = agent.invoke({"messages": [{"role": "user", "content": "Combien de jours de télétravail chez ACME ?"}]})
for message in result["messages"]:
    print(f"--- {type(message).__name__}")
    print(getattr(message, "tool_calls", None) or message.content[:300])
```

### Commande à exécuter

```powershell
python playground.py
```

### Résultat attendu

```text
--- HumanMessage
Combien de jours de télétravail chez ACME ?
--- AIMessage
[{'name': 'search_company_documents', 'args': {'query': 'jours de télétravail'}, 'id': ..., 'type': 'tool_call'}]
--- ToolMessage
--- Passage 1 --- Source : politique-teletravail.pdf, page ...
--- AIMessage
Les salariés éligibles peuvent télétravailler jusqu'à 2 jours par semaine ... Sources : ...
```

### Point pédagogique

C'est le **tool calling** : le 1er `AIMessage` ne contient pas de texte mais une
*demande* d'appel d'outil (nom + arguments JSON). LangChain exécute la fonction, renvoie
un `ToolMessage`, et le LLM rédige alors la réponse. Le LLM n'exécute jamais rien lui-même.

---

## 21. Ajouter les sources aux réponses

### Objectif

Afficher des sources **fiables**, issues des métadonnées et non du texte généré
(progression, étape 7 : ... → Réponse + sources).

### Fichiers concernés

`app/agent.py`

### Action

Ajouter `AgentAnswer`, `extract_sources` (qui lit les `ToolMessage.artifact`) et `ask`.

### Code à écrire

```python
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
```

Fichier complet `app/agent.py` :

```python
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
```

### Commande à exécuter

```powershell
python -c "from app.agent import *; from app.config import load_settings; from app.retrieval import load_vector_store; s = load_settings(); a = ask(create_documentation_agent(s, load_vector_store(s)), 'Quel est le plafond pour un repas professionnel ?'); print(a.text); print(a.sources)"
```

### Résultat attendu

```text
Le montant maximum remboursable pour un repas professionnel est de 25 euros par repas ...
['frais-professionnels.xlsx, feuille « Barèmes », ligne 2', ...]
```

### Point pédagogique

Deux niveaux de sources : la ligne « Sources : » écrite par le LLM (utile mais générée,
donc faillible) et la liste extraite des **artifacts** (métadonnées réelles, impossibles à
inventer). Leçon de prompt : la règle « Si les passages ne contiennent pas la réponse,
dis... » faisait refuser `llama3.1:8b` à tort ; « **Seulement si AUCUN passage**... » a
corrigé le problème.

---

## 22. Ajouter la gestion des erreurs

### Objectif

Remplacer les *stack traces* par des messages compréhensibles, et créer la CLI.

### Fichiers concernés

`app/config.py`, `app/cli.py`

### Action

1. Ajouter `OllamaNotReadyError` et `check_ollama` dans `app/config.py`.
2. Créer une première version de `app/cli.py` (sans Langfuse).

### Code à écrire

`app/config.py` :

```python
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
```

`app/cli.py` (version sans monitoring ; la version finale est donnée à l'étape 23) :

```python
"""Interface en ligne de commande.

    python -m app.cli
"""

from __future__ import annotations

import httpx
import ollama

from app.agent import AgentAnswer, ask, create_documentation_agent
from app.config import OllamaNotReadyError, check_ollama, load_settings
from app.retrieval import IndexNotFoundError, load_vector_store

BANNER = """
====================================
 ACME - Documentation Assistant
====================================
Posez votre question (ou 'quit' pour quitter).
"""

EXIT_COMMANDS = {"quit", "exit", "q"}


def print_answer(answer: AgentAnswer) -> None:
    print(f"\nAgent :\n{answer.text}\n")
    if answer.sources:
        print("Passages consultés (métadonnées) :")
        for source in answer.sources:
            print(f"- {source}")
    else:
        print("(Aucun passage documentaire consulté.)")
    print()


def main() -> None:
    settings = load_settings()
    try:
        check_ollama(settings)
        vector_store = load_vector_store(settings)
    except (OllamaNotReadyError, IndexNotFoundError) as error:
        raise SystemExit(f"Erreur : {error}")

    agent = create_documentation_agent(settings, vector_store)
    print(BANNER)

    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            continue
        if question.lower() in EXIT_COMMANDS:
            break
        try:
            print_answer(ask(agent, question))
        except (ConnectionError, httpx.ConnectError):
            print("\nErreur : Ollama ne répond plus. Vérifiez qu'il est lancé (`ollama serve`).\n")
        except ollama.ResponseError as error:
            print(f"\nErreur renvoyée par Ollama : {error.error}\n")

    print("Au revoir !")


if __name__ == "__main__":
    main()
```

### Commande à exécuter

Provoquer volontairement chaque erreur :

```powershell
$env:OLLAMA_MODEL="inexistant:1b"; python -m app.cli; Remove-Item Env:OLLAMA_MODEL
$env:CHROMA_DIR=".chroma-absent"; python -m app.cli; Remove-Item Env:CHROMA_DIR
$env:OLLAMA_BASE_URL="http://localhost:11999"; python -m app.cli; Remove-Item Env:OLLAMA_BASE_URL
# macOS/Linux : OLLAMA_MODEL=inexistant:1b python -m app.cli   (etc.)
```

### Résultat attendu

```text
Erreur : Le modèle Ollama 'inexistant:1b' n'est pas installé.
  -> Téléchargez-le avec : ollama pull inexistant:1b
Erreur : Aucun index trouvé dans ...\.chroma-absent.
  -> Lancez d'abord l'ingestion : python -m app.ingestion
Erreur : Ollama est injoignable sur http://localhost:11999.
  -> Lancez l'application Ollama ou `ollama serve`, puis réessayez.
```

### Point pédagogique

On vérifie les prérequis **au démarrage** plutôt que de découvrir le problème au milieu
d'une réponse. Pas de hiérarchie d'exceptions complexe : deux exceptions métier
(`OllamaNotReadyError`, `IndexNotFoundError`) et des messages qui disent **quoi faire**.
Les cas PDF illisible / Excel invalide sont gérés dans les loaders (étapes 9-10), et
« aucun document pertinent » dans l'outil (étape 19).

---

## 23. Ajouter Langfuse

### Objectif

Observer chaque exécution de l'agent (progression, étape 8 : tout le workflow → Langfuse).

### Fichiers concernés

`.env`, `app/observability.py`, `app/cli.py`

### Action

1. Créer un compte sur https://cloud.langfuse.com (région EU) ou https://us.cloud.langfuse.com (US),
   une organisation, un projet, puis *Project Settings → API Keys → Create new API keys*.
2. Renseigner `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` dans `.env`.
3. Créer `app/observability.py`.
4. Remplacer `app/cli.py` par sa version finale : handler dans `config={"callbacks": [...]}`,
   `propagate_attributes` pour la session et les tags, `flush` à la sortie.

### Code à écrire

`app/observability.py` :

```python
"""Monitoring avec Langfuse (SDK Python v4).

Langfuse s'intègre à LangChain via un callback handler : chaque étape exécutée
par LangChain (agent, appel LLM, appel d'outil) devient une observation dans
une trace Langfuse. Le SDK lit ses clés dans les variables d'environnement
LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY et LANGFUSE_BASE_URL.

Le monitoring est OPTIONNEL : sans clés, l'application fonctionne sans traces.
"""

from __future__ import annotations

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from app.config import Settings


def get_langfuse_handler(settings: Settings) -> CallbackHandler | None:
    """Retourne le handler Langfuse, ou None si Langfuse n'est pas utilisable."""
    if not settings.langfuse_enabled:
        print(
            "[langfuse] Non configuré (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY absents) : "
            "traçage désactivé."
        )
        return None

    try:
        # auth_check() fait un appel réseau : pratique en tutoriel pour détecter
        # tout de suite une mauvaise clé ou une mauvaise URL (à éviter en production).
        if not get_client().auth_check():
            raise RuntimeError("clés refusées")
    except Exception as error:
        # Les erreurs HTTP du SDK portent un status_code (401 = mauvaises clés ou mauvaise région)
        reason = getattr(error, "status_code", None) or type(error).__name__
        print(
            f"[langfuse] Connexion impossible à {settings.langfuse_base_url} ({reason}) : "
            "traçage désactivé.\n"
            "           Vérifiez les clés et LANGFUSE_BASE_URL (région EU/US) dans .env."
        )
        return None

    print(f"[langfuse] Traçage actif -> {settings.langfuse_base_url}")
    return CallbackHandler()


def flush_traces() -> None:
    """Envoie les traces en attente (le SDK les envoie par lots, en arrière-plan)."""
    get_client().flush()
```

`app/cli.py` (version finale) :

```python
"""Interface en ligne de commande.

    python -m app.cli
"""

from __future__ import annotations

import uuid
from contextlib import nullcontext

import httpx
import ollama
from langfuse import propagate_attributes

from app.agent import AgentAnswer, ask, create_documentation_agent
from app.config import OllamaNotReadyError, check_ollama, load_settings
from app.observability import flush_traces, get_langfuse_handler
from app.retrieval import IndexNotFoundError, load_vector_store

BANNER = """
====================================
 ACME - Documentation Assistant
====================================
Posez votre question (ou 'quit' pour quitter).
"""

EXIT_COMMANDS = {"quit", "exit", "q"}


def print_answer(answer: AgentAnswer) -> None:
    print(f"\nAgent :\n{answer.text}\n")
    if answer.sources:
        # Sources extraites des métadonnées des passages consultés par l'outil.
        print("Passages consultés (métadonnées) :")
        for source in answer.sources:
            print(f"- {source}")
    else:
        print("(Aucun passage documentaire consulté.)")
    print()


def main() -> None:
    settings = load_settings()

    # 1. Vérifications au démarrage : messages clairs plutôt que stack traces.
    try:
        check_ollama(settings)
        vector_store = load_vector_store(settings)
    except (OllamaNotReadyError, IndexNotFoundError) as error:
        raise SystemExit(f"Erreur : {error}")

    # 2. Assemblage de l'agent et du monitoring.
    agent = create_documentation_agent(settings, vector_store)
    langfuse_handler = get_langfuse_handler(settings)
    callbacks = [langfuse_handler] if langfuse_handler else []
    session_id = str(uuid.uuid4())  # regroupe les questions de cette session dans Langfuse

    print(BANNER)
    print(f"Modèle : {settings.ollama_model} | Embeddings : {settings.ollama_embedding_model}\n")

    # 3. Boucle question -> réponse.
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            continue
        if question.lower() in EXIT_COMMANDS:
            break

        # propagate_attributes (Langfuse v4) : ajoute session et tags à la trace.
        trace_context = (
            propagate_attributes(session_id=session_id, tags=["tutoriel", "cli"])
            if langfuse_handler
            else nullcontext()
        )
        try:
            with trace_context:
                answer = ask(agent, question, callbacks=callbacks)
            print_answer(answer)
        except (ConnectionError, httpx.ConnectError):
            print("\nErreur : Ollama ne répond plus. Vérifiez qu'il est lancé (`ollama serve`).\n")
        except ollama.ResponseError as error:
            print(f"\nErreur renvoyée par Ollama : {error.error}\n")

    if langfuse_handler:
        flush_traces()  # sinon les dernières traces peuvent être perdues à la sortie
    print("Au revoir !")


if __name__ == "__main__":
    main()
```

### Commande à exécuter

```powershell
python -m app.cli
```

### Résultat attendu

```text
[langfuse] Traçage actif -> https://cloud.langfuse.com
```

Sans clés : `[langfuse] Non configuré ... traçage désactivé.` et l'application fonctionne
quand même. Avec de mauvaises clés : `[langfuse] Connexion impossible ... (401)`.

### Point pédagogique

L'intégration passe par un **callback handler** : LangChain notifie le handler à chaque
étape (agent, LLM, outil), qui la transforme en observation Langfuse. L'agent n'est pas
modifié. API actuelle (SDK v4) : `from langfuse.langchain import CallbackHandler`,
variable `LANGFUSE_BASE_URL`, et `propagate_attributes(...)` qui remplace l'ancien
`update_trace`/`update_current_trace`. Le SDK envoie les traces **en arrière-plan, par
lots** : sans `flush()`, les dernières peuvent être perdues à la sortie du programme.

---

## 24. Vérifier les traces

### Objectif

Lire une trace et savoir diagnostiquer une mauvaise réponse.

### Fichiers concernés

Aucun (interface web Langfuse).

### Action

Poser 2 ou 3 questions dans la CLI, taper `quit`, puis ouvrir Langfuse → *Tracing*.

### Code à écrire

Aucun.

### Commande à exécuter

```powershell
python -m app.cli
> Quel est le montant maximum remboursable pour un repas professionnel ?
> quit
```

### Résultat attendu

Une trace par question, regroupées dans la même **session**, avec les tags `tutoriel`
et `cli`. Structure indicative (les noms exacts dépendent des versions) :

```text
Trace
└── agent
    ├── ChatOllama (generation) → décide d'appeler l'outil (tokens, durée)
    ├── search_company_documents (tool) → query + passages renvoyés
    └── ChatOllama (generation) → réponse finale (tokens, durée)
```

### Point pédagogique

- **Trace** : une requête complète. **Observation** : une étape (span, generation, tool...).
  **Session** : un groupe de traces.
- Diagnostic : réponse « je n'ai pas trouvé » à tort → le bon passage figure-t-il dans la
  sortie de l'outil ? Si non : problème de **retrieval** ; si oui : problème de **prompt/modèle**.
- Lenteur : comparer la durée des generations et celle de l'outil.
- Coût : nul en local, mais les **tokens** d'entrée montrent la taille du contexte injecté.

---

## 25. Ajouter les tests

### Objectif

Tester les composants **déterministes** sans dépendre du LLM.

### Fichiers concernés

`tests/conftest.py`, `tests/test_ingestion.py`, `tests/test_retrieval.py`, `tests/test_tools.py`

### Action

1. `conftest.py` : un faux modèle d'embeddings (`KeywordEmbeddings`) et des fixtures qui
   génèrent le corpus dans un dossier temporaire.
2. Tester l'ingestion, la recherche, les métadonnées et l'outil.
3. Isoler le test qui utilise le vrai modèle derrière le marqueur `ollama`.

### Code à écrire

`tests/conftest.py` :

```python
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
```

`tests/test_ingestion.py` :

```python
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
```

`tests/test_retrieval.py` :

```python
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
```

`tests/test_tools.py` :

```python
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
```

### Commande à exécuter

```powershell
pytest
pytest -m ollama
```

### Résultat attendu

```text
18 passed, 1 deselected in ~3s
1 passed, 18 deselected in ~15s
```

### Point pédagogique

> Les composants déterministes doivent être testés indépendamment du comportement
> probabiliste du LLM.

`KeywordEmbeddings` montre aussi ce qu'est un embedding : une fonction texte → vecteur.
Le test d'intégration vérifie ce qui est stable (l'outil a été appelé, la bonne source
a été consultée), **pas la formulation** de la réponse.

---

## 26. Lancer l'application complète

### Objectif

Enchaîner tout le pipeline depuis un état propre.

### Fichiers concernés

Tous.

### Action

Supprimer l'index, régénérer le corpus, réindexer, tester, lancer la CLI. Supprimer
`playground.py`.

### Code à écrire

Aucun.

### Commande à exécuter

```powershell
Remove-Item -Recurse -Force .chroma -ErrorAction SilentlyContinue   # macOS/Linux : rm -rf .chroma
Remove-Item playground.py -ErrorAction SilentlyContinue
python scripts/generate_corpus.py
python -m app.ingestion
pytest
python -m app.cli
```

### Résultat attendu

```text
====================================
 ACME - Documentation Assistant
====================================
Posez votre question (ou 'quit' pour quitter).

Modèle : llama3.1:8b | Embeddings : nomic-embed-text

> Quelle est la politique de télétravail ?

Agent :
La politique de télétravail d'ACME est la suivante : ... jusqu'à 2 jours par semaine ...

Sources :
- politique-teletravail.pdf, page 2
...

Passages consultés (métadonnées) :
- politique-teletravail.pdf, page 1
- politique-teletravail.pdf, page 2
...

> quit
Au revoir !
```

### Point pédagogique

Les deux pipelines sont bien séparés : `python -m app.ingestion` (hors ligne, une fois)
puis `python -m app.cli` (à chaque question). Les réponses varient légèrement d'une
exécution et d'une machine à l'autre : c'est normal avec un LLM.

---

## 27. Tester les questions de démonstration

### Objectif

Vérifier le comportement sur des cas concrets et identifier les limites.

### Fichiers concernés

`scripts/run_demo.py`, `examples/questions.md`, `examples/evaluation.md`

### Action

Écrire un script qui pose une liste de questions sans interaction, puis comparer les
réponses aux attendus de `examples/questions.md` et `examples/evaluation.md`.

### Code à écrire

`scripts/run_demo.py` :

```python
"""Pose les questions de démonstration à l'agent, sans interaction.

    python scripts/run_demo.py

Utile pour comparer deux prompts, deux modèles ou deux réglages de retrieval
sur les mêmes questions (voir examples/evaluation.md).
"""

from __future__ import annotations

import sys
import time
from contextlib import nullcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langfuse import propagate_attributes  # noqa: E402

from app.agent import ask, create_documentation_agent  # noqa: E402
from app.config import check_ollama, load_settings  # noqa: E402
from app.observability import flush_traces, get_langfuse_handler  # noqa: E402
from app.retrieval import load_vector_store  # noqa: E402

DEMO_QUESTIONS = [
    "Quelle est la politique de télétravail ?",
    "Quel est le montant maximum remboursable pour un repas professionnel ?",
    "Quelles sont les règles de télétravail et quelles règles de sécurité dois-je respecter ?",
    "Quelle est la politique concernant les véhicules de fonction ?",
    "Combien de jours de congés sont prévus par la politique de l'entreprise ?",
]


def main() -> None:
    settings = load_settings()
    check_ollama(settings)
    agent = create_documentation_agent(settings, load_vector_store(settings))
    handler = get_langfuse_handler(settings)

    for question in sys.argv[1:] or DEMO_QUESTIONS:
        start = time.perf_counter()
        context = propagate_attributes(tags=["demo"]) if handler else nullcontext()
        with context:
            answer = ask(agent, question, callbacks=[handler] if handler else [])
        duration = time.perf_counter() - start
        print("=" * 80)
        print(f"Q : {question}")
        print(f"({answer.tool_calls} appel(s) d'outil, {duration:.1f} s)\n")
        print(answer.text)
        print("\nPassages consultés :", "; ".join(answer.sources) or "aucun")

    if handler:
        flush_traces()


if __name__ == "__main__":
    main()
```

### Commande à exécuter

```powershell
python scripts/run_demo.py
python scripts/run_demo.py "À partir de quel montant faut-il 3 devis ?" "Quelle est la recette de la tarte aux pommes ?"
```

### Résultat attendu

| Question | Attendu |
|---|---|
| Politique de télétravail | 2 jours/semaine, accord du manager, 10 EUR/mois, VPN ; `politique-teletravail.pdf` |
| Plafond repas | 25 EUR par repas ; `frais-professionnels.xlsx`, feuille « Barèmes » |
| Télétravail + sécurité | Règles des deux documents ; `politique-teletravail.pdf` + `politique-securite.pdf` |
| Véhicules de fonction | « Je n'ai pas trouvé cette information... » |
| Jours de congés | 25 jours ouvrés (+ 10 RTT au forfait jours) ; `conges.pdf` |

### Point pédagogique

Un agent s'**évalue sur des cas concrets**, rejoués après chaque changement (modèle,
prompt, chunking, `TOP_K`). Pendant le développement de ce projet, c'est cette évaluation
qui a révélé deux problèmes : une règle de prompt trop stricte (étape 21) et un défaut de
retrieval corrigé par les préfixes de `nomic-embed-text` (étape 13). Pistes suivantes :
voir « Pour aller plus loin » dans le [README](README.md).
