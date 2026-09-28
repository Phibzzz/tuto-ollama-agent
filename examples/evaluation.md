# Mini-évaluation

Un agent ne se juge pas sur une démo réussie, mais sur un jeu de cas concrets
rejoué après chaque changement (modèle, prompt, chunking, `TOP_K`...).

Procédure manuelle (volontairement simple) :

1. `python scripts/run_demo.py "question 1" "question 2" ...`
2. Pour chaque cas, cocher : bonne information ? bonne source consultée ? pas d'invention ?
3. Noter le résultat avec la configuration utilisée (modèle, `TOP_K`, `MIN_SCORE`, version du prompt).

| # | Question | Source attendue | Information attendue |
|---|---|---|---|
| 1 | Quel est le nombre maximal de jours de télétravail ? | `politique-teletravail.pdf`, page 2 | 2 jours par semaine |
| 2 | Quel est le plafond de remboursement d'un repas professionnel ? | `frais-professionnels.xlsx`, feuille « Barèmes » | 25 EUR par repas |
| 3 | Quel est le plafond pour une nuit d'hôtel à Paris ? | `frais-professionnels.xlsx`, feuille « Barèmes » | 150 EUR par nuit |
| 4 | Combien de jours de congés payés par an ? | `conges.pdf`, page 1 | 25 jours ouvrés |
| 5 | Dans quel délai signaler un incident de sécurité ? | `politique-securite.pdf`, page 3 | 24 heures, à securite@acme.example |
| 6 | Quelle longueur minimale pour un mot de passe ? | `politique-securite.pdf`, page 1 | 12 caractères (+ MFA obligatoire) |
| 7 | À partir de quel montant faut-il 3 devis ? | `reglement-interieur.pdf`, page 2 | Achat supérieur à 1 000 EUR HT |
| 8 | Quelle est la politique concernant les véhicules de fonction ? | aucune | L'agent indique ne pas avoir trouvé l'information |

## Grille

| Critère | Question |
|---|---|
| Exactitude | L'information attendue est-elle présente et correcte ? |
| Traçabilité | La source attendue figure-t-elle dans les « Passages consultés » ? |
| Fidélité | La réponse contient-elle une information absente des documents ? |
| Refus | Pour le cas 8, l'agent reconnaît-il l'absence d'information ? |

Pour aller plus loin : automatiser cette grille (Langfuse *Datasets* & *Experiments*,
ou un script pytest qui vérifie la présence de mots-clés et de sources).
