# ADR-003 : Choix des frameworks et outils techniques

## Status
Proposé

## Date
2025-06-12

## Contexte

L’objectif est de constituer une stack technique cohérente, maintenable et reproductible pour développer des agents IA orchestrés via LangGraph, tout en permettant :

- Un démarrage rapide via les outils managés de la LangChain Platform.
- Une migration progressive vers une architecture full open-source et self-hostable.
- Un contrôle complet sur l'orchestration, la modularisation, l’observabilité et le monitoring à moyen terme.
- Une architecture maîtrisable par une petite équipe AI Engineering, compatible production.

---

## Décisions de stack technique (Phase 1 initiale)

| Composant | Choix validé | Raisons principales |
|-----------|--------------|---------------------|
| Gestion des dépendances | `uv` | Résolution rapide, gestion de lock simple, support du PEP 621 |
| Gestion des versions Python | `.python-version` (pyenv) | Verrouille la version locale (ex. 3.12.10) |
| Orchestration agents | `LangGraph` (open-source) | Orchestration explicite en graph de state machine, maîtrise de l’orchestration multi-agent |
| Plateforme initiale | `LangChain Platform (LangGraph Studio Cloud + LangServe Cloud + LangSmith)` | Permet l’exploration rapide sans setup d’infrastructure, vendor leverage contrôlé |
| Framework API | `LangServe` (Phase 1), migration prévue vers `FastAPI` (Phase 2) | Permet d’avancer rapidement tout en gardant la capacité de migration vers du self-host |
| LLM client SDK | `langchain-openai`, `langchain-anthropic`, `langchain-community` | Simplifie l’intégration multi-fournisseurs de LLM |
| Prompt management | Répertoire `prompts/` versionné dans Git | Simple, reproductible, auditable, permet d’amorcer une bibliothèque progressive |
| Vector store | `Qdrant` | Open-source, scalable, excellent support LangChain |
| Exploration initiale | `notebooks/` | Facilite l’expérimentation rapide, prototypage et tests exploratoires |
| Documentation projet | `docs/` (ADRs, structure, files, contributing, mocking) | Facilite la standardisation et l'onboarding client et développeur |
| IDE | `Cursor`, `Windsurf`, `VSCode` | Productivité optimisée sur code agentique, support LangGraph, notebooks, fast-refactor |

---

## Remarques complémentaires

- Cette stack permet un démarrage rapide en phase exploratoire tout en limitant la dette technique initiale.
- La séparation progressive des composants (`agents/`, `tools/`, `retrievers/`, `prompts/`, `models/`) sera structurée dès la phase 2.
- L’observabilité (Langfuse, Grafana, Prometheus) sera progressivement intégrée en phase 2 et au-delà.
- Les aspects CI/CD, sécurité, déploiement cloud et gestion fine des credentials seront traités en phase d’industrialisation.
- Les composants spécifiques au client (connecteurs CRM, DSP, scoring, génération persona, etc.) restent simulés en phase 1 (voir `docs/MOCKING.md`).

---

## Conséquences

- Mise en place rapide du socle technique exploratoire sous LangChain Platform.
- Capacité d’expérimentation rapide des flows métier sur LangGraph Studio Cloud.
- Architecture extensible et industrialisable sans refonte lourde.
- Permet la montée progressive des compétences techniques de l’équipe client.
- Aligne le projet sur les standards d’AI Engineering 2025 tout en gardant la capacité d’arbitrage cloud/on-prem selon les besoins de souveraineté.

