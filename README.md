# Company Documentation Agent

> Tutoriel de 2 heures : construire un **agent documentaire** capable de répondre
> aux questions des salariés d'une entreprise fictive (**ACME**) à partir de ses
> documents internes (PDF et Excel), avec un **LLM local (Ollama)**, **LangChain**,
> un **vector store local (Chroma)** et du **monitoring (Langfuse)**.

**Principe directeur** : ne pas construire le meilleur agent documentaire possible, mais
le plus petit agent permettant de comprendre correctement les concepts essentiels.

---

## Objectif

À la fin du tutoriel, vous saurez construire un agent qui :

1. reçoit une question en français ;
2. décide s'il doit interroger la documentation ;
3. appelle un **outil** de recherche documentaire ;
4. récupère les passages pertinents (PDF **et** Excel) ;
5. rédige une réponse avec le LLM local ;
6. cite ses **sources** (fichier + page, ou fichier + feuille + ligne) ;
7. est **observable** dans Langfuse (traces, appels LLM, outils, durées, tokens).

### Vocabulaire

| Terme | Définition courte |
|---|---|
| **LLM** | Modèle de langage qui génère du texte (ici `llama3.1:8b`, exécuté par Ollama). Il ne connaît pas vos documents. |
| **Prompt / instructions** | Texte qui cadre le comportement du LLM (le *system prompt* de l'agent). |
| **Outil (tool)** | Fonction Python que le LLM peut *demander* d'exécuter. Le LLM ne voit que son nom, sa description et ses paramètres. |
| **Agent** | LLM + instructions + outils + une boucle : le LLM décide d'appeler un outil, reçoit le résultat, puis répond. |
| **RAG** | *Retrieval-Augmented Generation* : on récupère des passages pertinents et on les donne au LLM pour qu'il réponde à partir d'eux. |
| **Retrieval** | L'étape de recherche des passages pertinents. |
| **Embeddings** | Représentation d'un texte sous forme de vecteur (liste de nombres). Deux textes de sens proche ont des vecteurs proches. |
| **Vector store** | Base qui stocke les vecteurs et retrouve les plus proches d'une question (ici Chroma). |
| **Contexte** | Tout ce que le LLM reçoit pour un appel : instructions, question, résultats des outils. |
| **Monitoring / tracing** | Enregistrement de chaque étape d'une exécution (qui a appelé quoi, avec quoi, combien de temps, combien de tokens). |

Dans ce projet, **RAG** et **agent** se combinent : la recherche documentaire (RAG) est
exposée comme un **outil**, et c'est l'**agent** qui décide quand l'utiliser.

---

## Architecture

```text
                    ┌──────────────────┐
                    │   Utilisateur    │  (CLI : python -m app.cli)
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │  Agent LangChain │  create_agent(model, tools, system_prompt)
                    │  - LLM Ollama    │  app/agent.py
                    │  - Instructions  │
                    │  - Outils        │
                    └────────┬─────────┘
                             ▼  tool call
                    ┌──────────────────┐
                    │ search_company_  │  app/tools.py
                    │ documents(query) │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ Retriever        │  app/retrieval.py
                    │ Chroma + embeds  │
                    └────────┬─────────┘
               ┌─────────────┴──────────────┐      (préparé à l'avance par
               ▼                            ▼       app/ingestion.py)
          PDF (pypdf)                  Excel (pandas)
          1 Document / page            1 Document / ligne
               └─────────────┬──────────────┘
                             ▼
              Documents normalisés (source, page | sheet, row, category)
                             ▼
                   Chunking (PDF uniquement)
                             ▼
               Embeddings (nomic-embed-text via Ollama)
                             ▼
                    Vector store Chroma (.chroma/)

 Toutes les étapes de l'agent (agent, LLM, outil) ──callbacks──► Langfuse
```

### Deux pipelines distincts

**Ingestion** (hors ligne, une fois, `python -m app.ingestion`) :

```text
Documents → Loaders → Normalisation → Chunking → Embeddings → Vector store
```

**Question utilisateur** (en ligne, à chaque question, `python -m app.cli`) :

```text
Question → Agent → Outil → Retriever → Passages pertinents → LLM Ollama → Réponse + sources
```

Séparer les deux est essentiel : on n'indexe pas les documents à chaque question,
et on peut tester/améliorer chaque pipeline indépendamment.

### Organisation du code

| Fichier | Responsabilité |
|---|---|
| [app/config.py](app/config.py) | Lire `.env`, exposer un objet `Settings`, vérifier qu'Ollama et les modèles sont disponibles. |
| [app/ingestion.py](app/ingestion.py) | Charger PDF/Excel/texte, normaliser les métadonnées, découper, remplir le vector store. |
| [app/retrieval.py](app/retrieval.py) | Embeddings, vector store, recherche, formatage des sources. |
| [app/tools.py](app/tools.py) | L'outil `search_company_documents` exposé à l'agent. |
| [app/agent.py](app/agent.py) | Le LLM, le *system prompt*, la création de l'agent, l'extraction des sources. |
| [app/observability.py](app/observability.py) | Langfuse (optionnel, désactivable). |
| [app/cli.py](app/cli.py) | Interface en ligne de commande. |
| [scripts/generate_corpus.py](scripts/generate_corpus.py) | Génère le corpus fictif (PDF + Excel). |
| [scripts/search_demo.py](scripts/search_demo.py) | Teste la recherche seule, sans agent. |
| [scripts/run_demo.py](scripts/run_demo.py) | Pose des questions à l'agent sans interaction (démo, évaluation). |

---

## Stack

| Composant | Choix | Version testée |
|---|---|---|
| Langage | Python | 3.13.10 (compatible 3.11+) |
| LLM local | Ollama + `llama3.1:8b` | Ollama 0.34.0 |
| Embeddings | Ollama + `nomic-embed-text` (v1.5) | — |
| Agent | `langchain` (`create_agent`) | 1.4.2 |
| Intégration Ollama | `langchain-ollama` (`ChatOllama`, `OllamaEmbeddings`) | 1.1.0 |
| Vector store | Chroma (`langchain-chroma`, `chromadb`) | 1.1.0 / 1.5.9 |
| Découpage | `langchain-text-splitters` | 1.1.2 |
| PDF | `pypdf` | 6.19.0 |
| Excel | `pandas` + `openpyxl` | 3.0.6 / 3.1.5 |
| Monitoring | `langfuse` (SDK Python v4) | 4.15.6 |
| Corpus fictif | `fpdf2` (PDF), `openpyxl` (Excel) | 2.8.8 |
| Tests | `pytest` | 9.1.1 |

Toutes les versions sont épinglées dans [requirements.txt](requirements.txt).

### APIs actuelles vs anciens tutoriels

Beaucoup de tutoriels en ligne utilisent des APIs qui ont changé. Ce projet utilise les APIs actuelles :

| Ancien (à éviter) | Actuel (utilisé ici) | Pourquoi |
|---|---|---|
| `initialize_agent`, `AgentExecutor`, `create_react_agent` | `from langchain.agents import create_agent` | LangChain v1 unifie la création d'agents autour de `create_agent`. |
| `from langchain_community.llms import Ollama` | `from langchain_ollama import ChatOllama` | Les intégrations sont dans des paquets dédiés ; `ChatOllama` supporte le tool calling. |
| `from langchain_community.vectorstores import Chroma` | `from langchain_chroma import Chroma` | Paquet d'intégration dédié. |
| `from langchain_community.document_loaders import PyPDFLoader` | `pypdf.PdfReader` directement | `langchain-community` est en fin de vie (il émet un `DeprecationWarning` à l'import). Lire un PDF avec pypdf prend 10 lignes et rend l'étape d'extraction visible. |
| Langfuse `from langfuse.callback import CallbackHandler` (SDK v2) | `from langfuse.langchain import CallbackHandler` (SDK v3/v4) | Le SDK est basé sur OpenTelemetry depuis la v3. |
| Langfuse `LANGFUSE_HOST` | `LANGFUSE_BASE_URL` | Nom de variable utilisé par la documentation actuelle. |
| Langfuse `CallbackHandler(update_trace=...)`, `update_current_trace(...)` | `propagate_attributes(session_id=..., tags=...)` | Changement du SDK v4. |

---

## Prérequis

- Python **3.11 ou plus** (`python --version`)
- **Ollama** installé ([ollama.com/download](https://ollama.com/download))
- ~6 Go de disque pour les modèles, 8 Go de RAM/VRAM recommandés pour `llama3.1:8b`
- (Optionnel) un compte **Langfuse Cloud** gratuit pour le monitoring

## Installation

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

```bash
cp .env.example .env        # Windows PowerShell : Copy-Item .env.example .env
```

| Variable | Rôle | Valeur par défaut |
|---|---|---|
| `OLLAMA_BASE_URL` | URL du serveur Ollama | `http://localhost:11434` |
| `OLLAMA_MODEL` | LLM de génération (doit supporter les *tools*) | `llama3.1:8b` |
| `OLLAMA_EMBEDDING_MODEL` | Modèle d'embeddings | `nomic-embed-text` |
| `DATA_DIR` / `CHROMA_DIR` | Corpus / index vectoriel | `data` / `.chroma` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | Découpage des PDF (en caractères) | `800` / `100` |
| `TOP_K` | Nombre de passages renvoyés par l'outil | `4` |
| `MIN_SCORE` | Pertinence minimale (0-1) d'un passage | `0.55` |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | Clés Langfuse (vide = monitoring désactivé) | — |
| `LANGFUSE_BASE_URL` | Région Langfuse | `https://cloud.langfuse.com` |

`.env` est ignoré par git (voir [.gitignore](.gitignore)) : n'y mettez jamais de secret versionné.

## Préparation d'Ollama

```text
Application Python → LangChain (ChatOllama) → API HTTP d'Ollama (localhost:11434) → Modèle local
```

LangChain ne fait qu'**orchestrer** : le modèle tourne sur votre machine, dans Ollama.
Aucune donnée ne quitte le poste (hormis les traces si Langfuse Cloud est activé).

```bash
ollama --version                 # 1. vérifier l'installation
ollama list                      # 2. vérifier que le serveur répond
ollama pull llama3.1:8b          # 3. LLM de génération (~4.9 Go)
ollama pull nomic-embed-text     # 4. modèle d'embeddings (~274 Mo)
ollama run llama3.1:8b "Dis bonjour en une phrase."   # 5. premier test
```

**Choix du modèle.** Un agent a besoin d'un modèle qui sait faire du **tool calling**
(produire un appel d'outil structuré au lieu de texte). Le critère n'est donc pas
seulement la taille. Liste des modèles compatibles : [ollama.com/search?c=tools](https://ollama.com/search?c=tools).

| Machine | Modèle suggéré | Remarque |
|---|---|---|
| 8 Go RAM/VRAM | `llama3.1:8b` (défaut) | Testé dans ce projet. |
| Plus modeste | `llama3.2:3b` | Plus rapide, tool calling moins fiable. |
| GPU confortable | `qwen3:8b`, `gpt-oss:20b`, ... | Souvent plus fiables en tool calling. |

Changer de modèle = modifier `OLLAMA_MODEL` dans `.env` et relancer `ollama pull`.
Refaire ensuite l'évaluation ([examples/evaluation.md](examples/evaluation.md)).

## Préparation du corpus

```bash
python scripts/generate_corpus.py
```

Génère un corpus **fictif** (aucune donnée réelle) :

```text
data/
├── rh/
│   ├── politique-teletravail.pdf   (3 pages : 2 j/semaine, indemnité 10 EUR, sécurité)
│   └── conges.pdf                  (2 pages : 25 jours + 10 RTT, report)
├── securite/
│   └── politique-securite.pdf      (3 pages : mots de passe, VPN, incidents)
├── finance/
│   └── frais-professionnels.xlsx   (feuilles « Barèmes » et « Procédure »)
└── entreprise/
    └── reglement-interieur.pdf     (2 pages : horaires, achats, comportement)
```

Il n'y a volontairement **aucune politique « véhicules de fonction »** : cela permet de
tester le comportement de l'agent face à une information absente.

## Ingestion

```bash
python -m app.ingestion
```

```text
20 documents chargés -> 20 chunks indexés
  - conges.pdf : 2 chunks
  - frais-professionnels.xlsx : 10 chunks
  ...
```

### PDF ≠ Excel : un point clé

| | PDF | Excel |
|---|---|---|
| Nature | Texte semi-structuré, organisé en **pages** | Données **tabulaires**, organisées en **lignes** et **colonnes** |
| Extraction | `pypdf.PdfReader(...).pages[i].extract_text()` | `pandas.read_excel(sheet_name=None)` → un `DataFrame` par feuille |
| Unité documentaire | 1 `Document` par page | 1 `Document` par **ligne** |
| Transformation | Aucune : le texte est déjà lisible | Chaque ligne devient une phrase autonome qui **répète les en-têtes** : `Feuille « Barèmes » - Catégorie : Repas professionnel ; Plafond (EUR) : 25 ; ...` |
| Découpage | Oui (`RecursiveCharacterTextSplitter`) | **Non** : une ligne est déjà une unité de sens ; la couper séparerait « Repas » de « 25 » |
| Métadonnées | `source`, `page`, `category` | `source`, `sheet`, `row`, `category` |

Traiter un Excel comme un PDF (tout concaténer en un bloc de texte, puis découper tous
les 800 caractères) donnerait des chunks où un montant est séparé de sa catégorie :
la recherche et la réponse deviendraient fausses.

### Chunking

Un LLM et un modèle d'embeddings ont une taille d'entrée limitée, et un passage court
et ciblé est mieux retrouvé qu'une page entière qui parle de tout.
`RecursiveCharacterTextSplitter` coupe d'abord sur les paragraphes, puis les lignes,
puis les mots, et **recopie les métadonnées dans chaque chunk** (la page reste connue).
Avec ce petit corpus, chaque page tient dans un chunk de 800 caractères.

### Embeddings et vector store

```text
Documents ──► Modèle d'embeddings ──► Vecteurs ──► Vector store (Chroma, .chroma/)
Question  ──► Modèle d'embeddings ──► Vecteur  ──► « quels vecteurs sont les plus proches ? »
```

> **Le modèle de génération et le modèle d'embeddings sont deux composants différents.**
>
> - LLM (`llama3.1:8b`) → génère la réponse.
> - Modèle d'embeddings (`nomic-embed-text`) → représente documents et questions sous forme vectorielle.
>
> Changer de modèle d'embeddings impose de **réindexer** tout le corpus.

**Recherche vectorielle** : on compare le vecteur de la question à ceux des passages
(ici avec la *distance cosinus*) et on renvoie les plus proches. Cela trouve des
passages proches **par le sens**, même sans mot commun exact.

`nomic-embed-text` exige des **préfixes de tâche** (`search_document:` pour les
documents, `search_query:` pour les questions, cf. sa fiche modèle). Sans eux, sur notre
évaluation, la question « À partir de quel montant faut-il 3 devis ? » ne retrouvait pas
`reglement-interieur.pdf`. C'est la classe `NomicEmbeddings` de `retrieval.py`.

**Pourquoi Chroma ?** Il s'installe avec `pip`, persiste dans un simple dossier, ne
nécessite aucun serveur, et dispose d'une intégration LangChain officielle.

## Retrieval

Testez la recherche **seule**, sans agent ni LLM :

```bash
python scripts/search_demo.py "plafond repas professionnel"
```

```text
[0.794] frais-professionnels.xlsx, feuille « Barèmes », ligne 2
        'Feuille « Barèmes » - Catégorie : Repas professionnel ; Plafond (EUR) : 25 ; ...'
```

Si le bon passage n'apparaît pas ici, **aucun prompt ne sauvera la réponse** : il faut
corriger l'ingestion, le chunking ou les embeddings.

`MIN_SCORE` écarte les passages vraiment trop éloignés. Mais avec un petit modèle
d'embeddings, une question hors sujet (« recette de la tarte aux pommes ») obtient
encore un score d'environ 0.7, proche de celui d'une question pertinente (environ 0.8).
**Un seuil ne suffit pas à détecter l'absence d'information** : c'est aussi le rôle
des instructions données au LLM.

## Agent

[app/agent.py](app/agent.py) :

```python
agent = create_agent(
    model=ChatOllama(model="llama3.1:8b", temperature=0),
    tools=[search_company_documents],
    system_prompt=SYSTEM_PROMPT,
)
result = agent.invoke({"messages": [{"role": "user", "content": question}]})
```

Le *system prompt* (en français, court, lisible en classe) impose de :
répondre en français, appeler l'outil pour toute question sur ACME, répondre
uniquement à partir des passages, dire quand l'information est absente, citer les
sources, signaler toute connaissance générale.

**Leçon observée pendant le développement** : une première version disait « Si les
passages ne contiennent pas la réponse, dis : Je n'ai pas trouvé… ». `llama3.1:8b`
répondait alors « je n'ai pas trouvé » même quand le bon passage était présent (repas,
congés). La reformulation « **Seulement si AUCUN passage** ne répond… » a corrigé le
problème. Avec un petit modèle, **la formulation du prompt se teste**, comme du code.

## Tool calling

```text
1. Question  ──► LLM : "Quel est le plafond d'un repas ?"
2. LLM       ──► AIMessage(tool_calls=[search_company_documents(query="plafond repas")])
3. LangChain ──► exécute la fonction Python ──► ToolMessage(content=passages, artifact=[Document...])
4. LLM       ──► lit les passages ──► réponse finale + « Sources : »
```

Le LLM **n'exécute rien** : il produit une *demande* d'appel (nom + arguments JSON).
C'est LangChain (la boucle de `create_agent`) qui exécute la fonction et renvoie le résultat.

Le LLM décide d'appeler l'outil à partir de **son nom, sa docstring et ses paramètres**
([app/tools.py](app/tools.py)). La docstring est donc un élément de prompt à soigner.

## Sources

Deux niveaux de sources sont affichés :

1. **Dans la réponse du LLM** (ligne `Sources :`) : demandé par le prompt. Utile, mais
   c'est du texte généré : un petit modèle peut en oublier ou en citer trop.
2. **« Passages consultés (métadonnées) »** affiché par la CLI : extrait des
   `ToolMessage.artifact`, c'est-à-dire des **métadonnées réelles** des documents
   renvoyés par l'outil. Ces sources ne peuvent pas être inventées.

L'outil utilise `response_format="content_and_artifact"` : il renvoie un texte pour le
LLM **et** les objets `Document` bruts pour le code applicatif.

```text
Agent :
Le montant maximum remboursable pour un repas professionnel est de 25 euros par repas...

Passages consultés (métadonnées) :
- frais-professionnels.xlsx, feuille « Barèmes », ligne 2
- ...
```

`format_source()` n'affiche une page ou une feuille **que si elle existe** dans les
métadonnées : on n'invente jamais de localisation.

## Monitoring avec Langfuse

### Pourquoi observer un agent ?

Un agent est une boîte noire probabiliste : pour une même question, il peut appeler ou
non un outil, avec une requête plus ou moins bonne, puis mal lire les passages. Sans
traces, on ne sait pas **à quelle étape** une mauvaise réponse est née.

### Concepts (modèle de données Langfuse)

- **Trace** : une requête complète, de la question à la réponse.
- **Observation** : une étape dans la trace, imbriquable. Types principaux :
  - **span** : une étape générique d'une durée donnée (ex. l'agent, la boucle) ;
  - **generation** : un appel LLM (entrée, sortie, modèle, **tokens**, durée) ;
  - **tool** : l'exécution d'un outil (arguments, résultat) ;
  - **event** : un événement ponctuel.
- **Session** : un regroupement de traces (ici toutes les questions d'une session CLI).

### Intégration (SDK Python v4)

```python
from langfuse import get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

handler = CallbackHandler()                       # lit LANGFUSE_* dans l'environnement
with propagate_attributes(session_id=session_id, tags=["tutoriel", "cli"]):
    agent.invoke({"messages": [...]}, config={"callbacks": [handler]})
get_client().flush()                              # envoie les traces avant de quitter
```

Le *callback handler* reçoit un événement à chaque étape exécutée par LangChain et le
transforme en observation Langfuse. Aucun changement dans l'agent n'est nécessaire.

### Mise en place (Langfuse Cloud)

1. Créer un compte sur [cloud.langfuse.com](https://cloud.langfuse.com) (région EU) ou
   [us.cloud.langfuse.com](https://us.cloud.langfuse.com) (région US).
2. Créer une organisation puis un projet.
3. *Project Settings → API Keys → Create new API keys*.
4. Copier les clés dans `.env` (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`) et
   ajuster `LANGFUSE_BASE_URL` à la région.
5. Lancer `python -m app.cli` : le message `[langfuse] Traçage actif` doit apparaître.

Alternative 100 % locale : Langfuse auto-hébergé avec Docker Compose (voir sources),
puis `LANGFUSE_BASE_URL=http://localhost:3000`.

### Ce qu'on observe dans une trace

Structure indicative (les noms exacts des observations dépendent des versions de
LangChain et du SDK Langfuse ; vérifiez-les dans votre propre trace) :

```text
Trace "acme-doc-agent"   (session, tags : tutoriel, cli)
└── agent (span)
    ├── model  → ChatOllama (generation)  : décide d'appeler l'outil, tokens, durée
    ├── tools  → search_company_documents (tool) : query, passages renvoyés
    └── model  → ChatOllama (generation)  : réponse finale, tokens, durée
```

### Ce que cela permet de diagnostiquer

| Symptôme | Où regarder dans la trace |
|---|---|
| Réponse inventée | L'outil a-t-il été appelé ? Les passages contenaient-ils l'information ? |
| « Je n'ai pas trouvé » à tort | Le bon passage était-il dans le résultat de l'outil ? (sinon : problème de retrieval) |
| Lenteur | Durée de chaque generation vs durée de l'outil |
| Coût / taille du contexte | Tokens d'entrée de la 2e generation (passages injectés) |
| Erreur | Observation en erreur (Ollama indisponible, exception dans l'outil) |

Les coûts sont nuls avec un modèle local ; les **tokens** restent visibles si Ollama les
renvoie. Sans clés, l'application fonctionne normalement, sans traces.

## Tests

```bash
pytest                 # 18 tests unitaires, SANS Ollama (< 5 s)
pytest -m ollama       # 1 test d'intégration avec le vrai modèle (nécessite l'index)
```

> **Les composants déterministes doivent être testés indépendamment du comportement
> probabiliste du LLM.**

| Fichier | Ce qui est testé |
|---|---|
| [tests/test_ingestion.py](tests/test_ingestion.py) | PDF → 1 document/page ; Excel → 1 document/ligne ; métadonnées ; Excel non découpé ; PDF/Excel corrompus ignorés |
| [tests/test_retrieval.py](tests/test_retrieval.py) | Requête → bon document ; seuil de score ; index absent ; formatage des sources |
| [tests/test_tools.py](tests/test_tools.py) | Description de l'outil ; `content` + `artifact` ; absence de résultat ; extraction des sources ; (intégration) agent réel |

Les tests de retrieval utilisent `KeywordEmbeddings` ([tests/conftest.py](tests/conftest.py)),
un **faux modèle d'embeddings** (sac de mots haché) : rapide, reproductible, sans Ollama.
Le test d'intégration vérifie ce qui est déterministe (l'outil a été appelé, la bonne
source consultée), pas la formulation exacte de la réponse.

### Gestion des erreurs

| Situation | Message |
|---|---|
| Ollama arrêté | `Ollama est injoignable sur http://localhost:11434. -> Lancez l'application Ollama ou ollama serve` |
| Modèle absent | `Le modèle Ollama 'xxx' n'est pas installé. -> ollama pull xxx` |
| Index absent | `Aucun index trouvé dans .chroma -> Lancez d'abord l'ingestion : python -m app.ingestion` |
| PDF illisible / Excel invalide | `[ingestion] PDF illisible, ignoré : ...` (l'ingestion continue) |
| Langfuse non configuré / mauvaises clés | `[langfuse] ... traçage désactivé.` (l'application continue) |
| Aucun passage pertinent | L'outil renvoie `Aucun document pertinent trouvé...` et l'agent le dit |

## Limites

Cette application est **volontairement pédagogique**. Limites connues :

- **Qualité des réponses dépendante du modèle** : `llama3.1:8b` est sensible à la
  formulation du prompt, cite parfois trop de sources, appelle parfois l'outil
  inutilement (ex. « Bonjour »).
- **Qualité des embeddings** : un petit modèle distingue mal un passage pertinent d'un
  passage hors sujet (scores proches) ; il est moins bon en français qu'en anglais.
- **Qualité du découpage** : taille fixe en caractères ; une page qui mélange plusieurs
  sujets produit un chunk « dilué ».
- **Hallucinations** : réduites par le prompt et les sources, jamais éliminées.
- **Limites du retrieval** : `TOP_K` fixe, pas de recherche hybride (mots-clés + vecteurs),
  pas de reranking, pas de reformulation de requête.
- **Excel complexes** : cellules fusionnées, plusieurs tableaux par feuille, formules,
  en-têtes sur plusieurs lignes ne sont pas gérés.
- **Tableaux dans les PDF** : l'extraction texte de pypdf perd la structure des tableaux ;
  les PDF scannés (images) nécessitent de l'OCR.
- **Pas de contrôle d'accès documentaire** : tout utilisateur voit tout le corpus.
- **Pas de sécurité avancée** (injection de prompt via un document, filtrage des sorties).
- **Pas de gestion multi-utilisateurs** ni de mémoire de conversation.
- **Vector store local** : réindexation complète à chaque ingestion.
- **Monitoring simplifié** : pas d'alertes, pas de scores de qualité automatiques.

Un véritable système documentaire d'entreprise nécessiterait probablement : gestion des
droits, authentification, filtrage des documents par utilisateur, gouvernance
documentaire (versions, propriétaires, dates de validité), indexation incrémentale,
contrôle qualité de l'extraction, évaluation automatique continue, observabilité avancée.

## Pourquoi pas LangGraph ?

**Avons-nous besoin de LangGraph ?**

| Critère | Notre besoin | LangGraph nécessaire ? |
|---|---|---|
| Nombre d'étapes | Une boucle « LLM → outil → LLM » | Non : fournie par `create_agent` |
| État | L'historique des messages | Non : géré par `create_agent` |
| Boucles | Répéter les appels d'outil jusqu'à la réponse | Non : c'est la boucle standard d'agent |
| Branchements | Aucun branchement métier explicite | Non |
| Persistance | Aucune (chaque question est indépendante) | Non |
| Orchestration | Un seul agent, un seul outil | Non |

**Réponse : non.** LangGraph n'est volontairement pas utilisé dans cette version car
LangChain fournit suffisamment d'abstractions pour le workflow pédagogique présenté.

Précision honnête : `create_agent` est lui-même construit sur le *runtime* de LangGraph
(le paquet `langgraph` est installé comme dépendance de `langchain`). Mais nous n'écrivons
**aucun graphe**, aucun nœud, aucun état personnalisé.

LangGraph deviendrait pertinent pour : un workflow imposé (ex. classer la question →
rechercher → vérifier la réponse → reformuler si besoin), une validation humaine
(*human-in-the-loop*), plusieurs agents spécialisés, ou une conversation persistante
avec reprise.

## Reproduire le tutoriel

- **Pas à pas, from scratch** : [instructions-dev.md](instructions-dev.md) (27 étapes,
  chacune avec objectif, fichiers, code, commande, résultat attendu et point pédagogique).
- **Questions de démonstration** : [examples/questions.md](examples/questions.md).
- **Mini-évaluation** : [examples/evaluation.md](examples/evaluation.md).

Démarrage rapide avec le code final :

```bash
pip install -r requirements.txt
cp .env.example .env
ollama pull llama3.1:8b && ollama pull nomic-embed-text
python scripts/generate_corpus.py
python -m app.ingestion
pytest
python -m app.cli
```

### Déroulé des 2 heures

| Temps | Séquence | Étapes de `instructions-dev.md` | Progression |
|---|---|---|---|
| 0-10 min | Introduction : problème, architecture, LLM / RAG / agent | 0 | — |
| 10-20 min | Ollama + LangChain : premier appel | 1-6, 17 | Ollama → LLM ; Ollama → LangChain → LLM |
| 20-40 min | Ingestion : PDF, Excel, normalisation, chunking | 7-12 | Documents → Loader → Documents LangChain |
| 40-60 min | Embeddings + vector store | 13-14 | Chunks → Embeddings → Vector store |
| 60-75 min | Retriever testé seul | 15-16 | Question → Retriever → Documents |
| 75-95 min | Agent + outil + sources | 18-22 | Question → Agent → Tool → Retriever → LLM → Réponse + sources |
| 95-110 min | Langfuse | 23-24 | Tout le workflow → Langfuse |
| 110-120 min | Démonstration, tests, limites | 25-27 | — |

## Sources officielles

Documentation effectivement consultée pour ce projet (septembre 2026) :

**LangChain**
- Agents (`create_agent`) : https://docs.langchain.com/oss/python/langchain/agents
- Tools (`@tool`) : https://docs.langchain.com/oss/python/langchain/tools
- `response_format` des outils : https://reference.langchain.com/python/langchain-core/tools/base/BaseTool/response_format
- `ToolMessage.artifact` : https://reference.langchain.com/python/langchain-core/messages/tool/ToolMessage/artifact
- ChatOllama : https://docs.langchain.com/oss/python/integrations/chat/ollama
- OllamaEmbeddings : https://docs.langchain.com/oss/python/integrations/text_embedding/ollama
- Chroma : https://docs.langchain.com/oss/python/integrations/vectorstores/chroma
- Text splitters : https://docs.langchain.com/oss/python/integrations/splitters
- Fin de vie de `langchain-community` : https://github.com/langchain-ai/langchain-community/issues/674

**Ollama**
- Quickstart : https://docs.ollama.com/quickstart
- Tool calling : https://docs.ollama.com/capabilities/tool-calling
- Embeddings : https://docs.ollama.com/capabilities/embeddings
- Modèles compatibles tools : https://ollama.com/search?c=tools
- nomic-embed-text : https://ollama.com/library/nomic-embed-text
- Fiche modèle Nomic (préfixes de tâche) : https://huggingface.co/nomic-ai/nomic-embed-text-v1.5

**Langfuse**
- Intégration LangChain : https://langfuse.com/integrations/frameworks/langchain
- Migration SDK Python v3 → v4 : https://langfuse.com/docs/observability/sdk/upgrade-path/python-v3-to-v4
- Modèle de données (trace, observation, session) : https://langfuse.com/docs/observability/data-model
- Auto-hébergement Docker Compose : https://langfuse.com/self-hosting/docker-compose

**Formats et stockage**
- pypdf, extraction de texte : https://pypdf.readthedocs.io/en/stable/user/extract-text.html
- pandas `read_excel` : https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html
- openpyxl : https://openpyxl.readthedocs.io/en/stable/
- Chroma : https://docs.trychroma.com/docs/overview/introduction
- Python `venv` : https://docs.python.org/3/library/venv.html

## Pour aller plus loin

1. **Filtrer par catégorie** : ajouter un paramètre `category` à l'outil
   (`filter={"category": "rh"}` dans Chroma), pour montrer l'usage des métadonnées.
2. **Recherche hybride** (BM25 + vecteurs) et **reranking** pour mieux distinguer les passages.
3. **Meilleur modèle d'embeddings** : `embeddinggemma` ou `qwen3-embedding` (recommandés
   par la documentation Ollama), à comparer avec [examples/evaluation.md](examples/evaluation.md).
4. **Outil Excel dédié** : interroger le `DataFrame` directement (filtre, calcul) plutôt
   que par similarité, pour des questions comme « quel est le plafond le plus élevé ? ».
5. **Mémoire de conversation** : `checkpointer` de `create_agent` + `thread_id`.
6. **Évaluation automatisée** : Langfuse *Datasets* / *Experiments*, ou un script pytest.
7. **Interface web** : Streamlit (`st.chat_input`) en réutilisant `ask()` tel quel.
8. **Contrôle d'accès** : filtrer les documents selon les droits de l'utilisateur.
9. **LangGraph** : si un workflow explicite devient nécessaire (voir section dédiée).
