# Questions de démonstration

Chaque question illustre un cas précis. Les réponses attendues correspondent au
corpus fictif généré par `scripts/generate_corpus.py`.

Lancer les 5 questions d'un coup :

```bash
python scripts/run_demo.py
```

---

## 1. Question PDF

```text
Quelle est la politique de télétravail ?
```

- **Ce qu'on démontre** : recherche dans un PDF, synthèse de plusieurs pages.
- **Attendu** : jusqu'à 2 jours par semaine, volontariat + accord du manager, après la période d'essai, jours fixes, indemnité de 10 EUR/mois, VPN obligatoire.
- **Sources attendues** : `politique-teletravail.pdf`, pages 1 à 3.

## 2. Question Excel

```text
Quel est le montant maximum remboursable pour un repas professionnel ?
```

- **Ce qu'on démontre** : une donnée tabulaire (une ligne Excel) retrouvée par recherche vectorielle.
- **Attendu** : 25 EUR par repas (50 EUR par personne en cas d'invitation d'un client).
- **Source attendue** : `frais-professionnels.xlsx`, feuille « Barèmes », ligne 2.

## 3. Question croisée

```text
Quelles sont les règles de télétravail et quelles règles de sécurité dois-je respecter ?
```

- **Ce qu'on démontre** : une réponse qui combine plusieurs documents.
- **Attendu** : règles de télétravail + VPN obligatoire, pas de Wi-Fi public sans VPN, écran verrouillé, pas d'impression de documents confidentiels au domicile.
- **Sources attendues** : `politique-teletravail.pdf` et `politique-securite.pdf` (page 2).

## 4. Information absente

```text
Quelle est la politique concernant les véhicules de fonction ?
```

- **Ce qu'on démontre** : l'agent doit dire qu'il ne sait pas, au lieu d'inventer.
- **Attendu** : « Je n'ai pas trouvé cette information dans la documentation ACME. »
- **Remarque** : l'outil renvoie quand même des passages (les plus proches, mais hors sujet) : c'est le LLM qui doit juger qu'ils ne répondent pas.

## 5. Question nécessitant une source

```text
Combien de jours de congés sont prévus par la politique de l'entreprise ?
```

- **Ce qu'on démontre** : une réponse chiffrée qui doit être justifiée par une source.
- **Attendu** : 25 jours ouvrés de congés payés par an (+ 10 jours de RTT pour les salariés au forfait jours).
- **Source attendue** : `conges.pdf`, page 1.

---

## Questions bonus

| Question | Attendu | Source |
|---|---|---|
| Faut-il des devis pour un achat de 2000 euros ? | Oui, 3 devis + validation du service Achats (> 1 000 EUR HT) | `reglement-interieur.pdf`, page 2 |
| Quel est le délai pour soumettre une note de frais ? | 3 mois maximum | `frais-professionnels.xlsx`, feuille « Procédure » |
| Quelle est la recette de la tarte aux pommes ? | Hors sujet : l'agent ne doit pas répondre à partir de ses connaissances générales | aucune |
| Bonjour, qui es-tu ? | Présentation de l'assistant (observer dans Langfuse s'il appelle l'outil inutilement) | aucune |
