# Feuille de route projet Oryjin AI Agent

---

## Vision globale de la trajectoire

Le projet est organisé en deux phases successives, pour un total de 13,75 jours répartis comme suit :

| Phase   | Durée      | Objectif général                                                                            |
| ------- | ---------- | ------------------------------------------------------------------------------------------- |
| Phase 1 | 5 jours    | Mise en place du socle technique et prototype initial avec la LangChain Platform            |
| Phase 2 | 8,75 jours | Construction progressive du socle cible avec le client (pair programming et modularisation) |

---

## Phase 1 — Exploration, cadrage et prototype rapide (5 jours)

### Objectif principal

* Avoir une démonstration pour le 20 juin
* Définir la trajectoire technique et fonctionnelle du projet.
* Poser les fondations techniques initiales.
* Réaliser un premier POC fonctionnel avec un graphe exécuté sous LangChain Platform (LangGraph Studio Cloud et LangServe Cloud).
* Lancer la réflexion structurante sur le choix du LLM et la stratégie d’orchestration.

### Répartition des 5 jours

| Activité                                   | Durée         |
| ------------------------------------------ | ------------- |
| Exploration collaborative                  | 2 x ½ journée |
| Cadrage technique (solo)                   | 1 jour        |
| Développement initial                      | 3 jours       |

### Contenu technique livré en fin de phase 1

Initialisation du socle technique :

* pyproject.toml avec uv
* uv.lock généré
* requirements_no_versions_dev_only.txt et requirements_no_versions créés
* Makefile avec les commandes de base
* .env.example préparé
* .gitignore, .dockerignore configurés
* .python-version verrouillé (ex : 3.12.10)
* notebook d'exploration

Travaux de cadrage structurants :

* LLM : API Mistral à définir
* Adoption du style fonctionnel pour la construction des nodes du graphe.
* Premiers travaux sur la gestion des prompts : premiers essais et amorce de future bibliothèque de prompts.
* Rédaction des ADR initiaux :
  * 000-processus-adr.md
  * 001-language-strategy.md
  * 002-python-choice.md
  * 003-framework-and-tooling-selection.md

Développement fonctionnel (POC LangChain Platform) :
* Exemple graph (template sur une autre problématique)
* Construction d’un premier graphe couvrant les grandes étapes métier.
* Utilisation de LangGraph Studio Cloud pour la modélisation des flows.
* Déploiement via LangServe Cloud.
* Mocking contrôlé des dépendances externes (CRM, segmentation, scoring DSP, génération visuelle).
* Documentation initiale de l'orchestration.

Arborescence de travail en phase 1 :

```
.
├── app/
│   ├── demo/
│   └── core/
│       ├── langgraph.json/
│       ├── .env
│       └── studio/
│           ├── agent.py
│           ├── tools.py
│           └── mock.py
├── notebooks/
├── docs/
│   ├── ADR/
│   ├── prompts/
│   └── exploration/
├── README.md
├── ROADMAP.md
├── pyproject.toml
├── uv.lock
├── Makefile
├── requirements_no_versions_dev_only.txt
├── requirements_no_versions.txt
├── .env.example
├── .gitignore
└── .python-version
```

### Livrables
- Démonstration via LangGraph Studio sur le use case DSP partiellement mocké. voir MOCKING.md
- Repository du projet

---

## Phase 2 — Construction modulaire et co-développement (8,75 jours)

### Objectif principal

* Industrialiser progressivement l’architecture avec le client en pair programming.
* Migrer les composants critiques vers des briques open-source contrôlables.
* Approfondir la gestion des prompts et construire une bibliothèque structurée.

### Répartition détaillée de la phase 2

| Activité                                | Durée      |
| --------------------------------------- | ---------- |
| Pair programming                        | 7 jours    |
| Préparation et consolidation (divers)   | 1,75 jours |
| - Préparation des sessions              | 1 jour     |
| - Revue finale du code et documentation | 0,75 jour  |

### Deux trajectoires possibles pour la phase 2

#### Alternative 1 : Architecture open-source et industrialisation

* Migration LangServe vers FastAPI.
* Migration LangSmith vers Langfuse (self-host).
* Déploiement local de LangGraph Studio.
* Modularisation complète (agents / tools / retrievers / prompts / api / tests).
* Structuration docker-compose.yml (Qdrant, Langfuse, Grafana, Prometheus).
* Construction progressive de la bibliothèque de prompts pour les différents agents.
* Préparation pour une intégration sur le Snowflake marketplace

##### Avantages :

* Architecture robuste, souveraine, maintenable.
* Compatible production et industrialisation progressive.
* Forte montée en compétence interne.

##### Inconvénients :

* Moins de fonctionnalités métier livrées dans la période impartie.
* Besoin d'investissement technique plus important sur la stack.

#### Alternative 2 : Accélération fonctionnelle sur le cas d’usage DSP

* Intégration progressive des étapes métier mockées en phase 1.
* Implémentation des connecteurs CRM réels, scoring lookalike, segmentation ML, connexions DSP.
* Maintien temporaire de certaines dépendances LangChain Platform (LangServe, LangSmith).

##### Avantages :

* Délivrables fonctionnels plus rapides et visibles.
* Sécurisation rapide du delivery métier.

##### Inconvénients :

* Vendor lock-in partiel.
* Industrialisation décalée à une phase 3.


## Tableau de périmètre des fonctionnalités

| Fonctionnalité | Description | Inclus dans le périmètre actuel |
|------------------|-------------|-------------------------|
| Modélisation du graphe (partiellement mocké voir MOCKING.md) | Construction du graphe conversationnel agent avec LangGraph | Oui |
| ADR documentés | Création et versionning des décisions d’architecture | Oui |
| Stack technique initiale | uv, pyproject.toml, Makefile, env, ADR, ROADMAP, Mocking | Oui |
| Utilisation de LangChain Platform (LangServe + LangGraph Studio Cloud + LangSmith) | Déploiement exploratoire rapide pour POC fonctionnel | Oui |
| Exploration initiale des prompts | Amorçage de la bibliothèque de prompts versionnés | Oui |
| Mocking des dépendances externes | API CRM, scoring, DSP, génération persona, visuels | Oui |
| Migration FastAPI | Remplacement de LangServe par une API FastAPI | Oui |
| Migration Langfuse | Remplacement de LangSmith par Langfuse self-host | Non |
| Dockerisation complète | Stack Qdrant, Langfuse, Grafana, Prometheus | Uniquement Snowflake |
| Modularisation code | Découpage agents, tools, retrievers, prompts, API, tests | Non |
| Tracing agents local | Monitoring des runs agents avec Langfuse | Langsmith |
| Connecteurs CRM réels | Implémentation de l’accès aux API CRM réelles | Non |
| Segmentation ML | Intégration d’un modèle de segmentation | Simplifié |
| Scoring lookalike | Implémentation scoring géographique avancé | Non |
| Génération visuelle persona | Génération IA des personas en image | Oui Simplifié |
| Mapping DSP | Transformation des critères pour la DSP | Oui Simplifié |
| Connexion API DSP | Déploiement des briefs DSP directement sur la plateforme | Non |
| Snowflake marketplace | Étude et cadrage intégration sur la marketplace Snowflake | Oui |
| Sécurité et authentification | Gestion des credentials, secret management | Non |
| CI/CD | Déploiement continu, tests automatisés | Non |


---

## Limites de périmètre après 13,75 jours

À l'issue de cette enveloppe, les éléments suivants resteront à adresser dans des phases ultérieures :

* CI/CD complet.
* Sécurisation des accès et gestion des credentials.
* Mise en production des workflows multi-agents.
* Optimisation de la gestion des prompts et des agents complexes.
* Monitoring de production.
* Sécurisation juridique et conformité des accès aux données CRM réelles.
* [À compléter]

---

## Planning prévisionnel des interventions 12,75 (+1 jour de préparation hors calendrier)
| Date prévisionnelle | Phase | Type d'intervention | Durée | Qui | Sujet |
|---------------------|-------|---------------------|-------|------|--------|
| 12/06/2025 | 1 | Cadrage du projet | 1 jour | Jérémy | Cadrage technique, choix de stack, organisation roadmap |
| 13/06/2025 | 1 | Exploration | ½ jour | Jérémy, Nicolas, Lanwenn, Mihiare | Présentation architecture cible, cadrage fonctionnel initial |
| 16/06/2025 | 1 | Exploration | ½ jour | Jérémy, Nicolas, Lanwenn, Mihiare | mock des données, et de l'enrichissement + structuré instruction DSP|
| 18/06/2025 | 1 | Programmation | 1 jour | Jérémy | Setup du socle technique initial (uv, pyproject, Makefile, ADR) |
| 19/06/2025 | 1 | Programmation | 1 jour | Jérémy | Prototypage LangGraph Studio Cloud, premiers flows agents |
| 20/06/2025 | 1 | Programmation | 1 jour | Jérémy | Construction du graphe complet mocké, préparation démo Phase 1 |
| 09/07/2025 | 2 | Programmation | 1 jour | Jérémy, Lanwenn, Mihiare | Démarrage migration FastAPI, explication architecture |
| 10/07/2025 | 2 | Programmation | 1 jour | Jérémy, Lanwenn, Mihiare | Refactor agents et tools, separation des modules |
| 11/07/2025 | 2 | Programmation | 1 jour | Jérémy, Lanwenn, Mihiare | Intégration prompts, amorce bibliothèque de prompts |
| 15/07/2025 | 2 | Programmation | 1 jour | Jérémy, Lanwenn, Mihiare | Implémentation retrievers, connecteurs CRM simulés |
| 16/07/2025 | 2 | Programmation | 1 jour | Jérémy, Lanwenn, Mihiare | Préparation docker-compose, intégration Langfuse local |
| 17/07/2025 | 2 | Programmation | 1 jour | Jérémy, Lanwenn, Mihiare | Consolidation workflows, revue du graphe global |
| 18/07/2025 | 2 | Restitution | 0,75 jour | Jérémy, Nicolas, Lanwenn, Mihiare | Démonstration, bilan, cadrage des suites possibles |

---

## Références

L’ensemble des décisions structurantes est consigné dans les ADR versionnés sous `docs/ADR/`.

