# ADR-001: Choix de version Python

## Status
Proposé

### Date
2025-06-12

## Contexte
Le choix de version Python impacte :

* La stabilité des bibliothèques IA/LLM (LangGraph, LangChain, FastAPI, etc.)
* La maintenance des environnements (CI/CD, Docker, cloud)
* La durée de support long terme (correctifs et sécurité)

Le projet vise une base robuste, moderne et stable compatible avec l’écosystème AI Engineering 2025-2028.

## Rappels : cycle de vie officiel des versions Python
Référence officielle : [https://devguide.python.org/versions/](https://devguide.python.org/versions/)

Chaque version majeure de Python suit 3 grandes phases :

| Phase             | Durée approximative                | Description                                                           |
| ----------------- | ---------------------------------- | --------------------------------------------------------------------- |
| **Prerelease**    | \~5 mois avant release officielle  | Période de beta et RC. Instable, non adaptée à la production.         |
| **Bugfix**        | \~18 mois après release officielle | Correctifs de bugs et améliorations mineures. Évolutif mais stable.   |
| **Security**      | \~42 mois après la fin de bugfix   | Correctifs de sécurité uniquement. Évolutif figé, stabilité maximale. |
| **Support total** | \~5 ans                            | Cycle complet du support officiel d’une version.                      |

---

## Situation actuelle (mi-2025)
| Version | Release  | Phase actuelle | Fin bugfix | Fin security | Support restant |
| ------- | -------- | -------------- | ---------- | ------------ | --------------- |
| 3.11    | Oct 2022 | **Security**   | Oct 2024   | Oct 2027     | \~33 mois       |
| 3.12    | Oct 2023 | **Security**   | Mai 2025   | Oct 2028     | \~45 mois       |
| 3.13    | Oct 2024 | **Bugfix**     | Mai 2026   | Mai 2029     | \~57 mois       |

---

## Décision
**Version retenue : Python 3.12.10**

* Version de référence : 3.12.10
* Plage définie dans `pyproject.toml` : `>=3.12,<3.13`

---

## Justification détaillée

### Python 3.13 (actuellement en phase Bugfix)

* ✅ Période de support la plus longue
* ✅ Nouveautés syntaxiques (ex: `except*`, nouveaux protocoles typing, performances)
* ❌ Déploiement récent, certaines bibliothèques IA et data sont encore en adaptation
* ❌ Risque d’instabilité résiduelle sur certaines librairies d’écosystème LLM

### Python 3.12 (actuellement en phase Security)

* ✅ 15 mois de maturité en production
* ✅ Large adoption par les principaux frameworks AI / LLM
* ✅ Aucun problème de compatibilité connu à date
* ✅ Stabilité maximale pour production
* ✅ Support de sécurité jusqu’à Octobre 2028
* ❌ Aucun ajout de fonctionnalité future (stabilité figée)

### Python 3.11 (Security avancé)

* ✅ Très stable
* ❌ Cycle de support restant plus court (\~33 mois)
* ❌ Manque certaines optimisations de 3.12

---

## Conséquences de ce choix

* ✅ Sécurité, stabilité, compatibilité large IA en 2025
* ✅ Moins de maintenance liée aux upgrades de librairies
* ✅ Alignement avec écosystèmes cloud et containerisés
* ❌ Obligation de planifier une montée de version vers 3.13/3.14 à horizon 2027-2028

---

## Alignement des environnements techniques

| Outil               | Paramètre         | Valeur                |
| ------------------- | ----------------- | --------------------- |
| `pyproject.toml`    | `requires-python` | `>=3.12,<3.13`        |
| `pyenv` (local dev) | version           | `3.12.10`             |
| `Docker`            | image             | `python:3.12.10-slim` |
| `CI/CD`             | runtime           | `3.12.10`             |
