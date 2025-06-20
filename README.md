# Projet Oryjin AI Agent

Ce dépôt contient les travaux pour la construction d'un agent conversationnel métier, orchestré avec LangGraph, destiné à l'accompagnement des campagnes marketing.

## Installation et Lancement

Suivez ces étapes pour configurer et lancer l'application en local.

### Prérequis
- Python 3.12

### 1. Installation de `uv` (Optionnel mais recommandé)

`uv` est un installateur de paquets et un gestionnaire d'environnements virtuels Python, écrit en Rust. Il est extrêmement rapide et peut remplacer `pip` et `venv`.

```bash
# Sur macOS et Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Pour les autres systèmes d'exploitation, veuillez consulter la [documentation officielle de `uv`](https://github.com/astral-sh/uv).

### 2. Création et activation de l'environnement virtuel

Depuis la racine du projet, créez et activez un environnement virtuel.

**Avec `uv` :**
```bash
# Crée un environnement virtuel dans le dossier .venv
uv venv

# Active l'environnement
source .venv/bin/activate
```

**Avec `venv` (méthode standard) :**
```bash
# Crée l'environnement
python3 -m venv .venv

# Active l'environnement
source .venv/bin/activate
```

### 3. Installation des dépendances

Installez les paquets Python requis.

**Avec `uv` :**
```bash
uv pip install -r requirements.txt
```

**Avec `pip` :**
```bash
pip install -r requirements.txt
```

### 4. Lancement du serveur de développement

Une fois les dépendances installées, naviguez dans le dossier de l'application et lancez le serveur LangGraph.

```bash
# Naviguez vers le dossier de l'application
cd app/core/studio

# Lancez le serveur en mode développement
langgraph dev
```

Le serveur sera alors accessible, généralement à l'adresse [http://127.0.0.1:8000](http://127.0.0.1:8000). Vous pourrez interagir avec l'API et l'interface utilisateur de LangGraph.