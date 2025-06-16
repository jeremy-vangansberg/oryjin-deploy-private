# Guide de contribution — AI Agents Engineering

## Objectif

Garantir la qualité du code et la reproductibilité des expérimentations IA.

## Principes

- Respecter la structure modulaire existante (`app/agents/`, `tools/`, `prompts/`, etc.)
- Chaque PR doit contenir :
  - Tests unitaires associés
  - Documentation à jour (README local, prompts versionnés)
  - Si besoin, un ADR pour tout changement structurant

## Workflow classique

- Créer une branche `feature/nom-fonctionnalité`
- Lancer les tests avant PR (`make test`)
- Lancer les linters avant PR (`make lint`)
- Documenter les nouveaux prompts dans `app/prompts/`

## Standards outils

- Python 3.12.10 (locked)
- Gestion dépendances via `uv`
- Linting via `ruff`
- Type checking via `mypy`
- Testing via `pytest`

## Standards de code

- Conventions de nommage LangGraph appliquées
- Typage explicite recommandé (Pydantic, TypedDict, BaseModel)
- Documentation minimale dans chaque `agents/`, `tools/`, `prompts/` via README local
