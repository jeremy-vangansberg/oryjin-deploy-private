****# ADR-001: Stratégie linguistique du projet

## Status
Proposé

## Context
Notre équipe est francophone et développe une solution pour des utilisateurs francophones, mais nous évoluons dans un écosystème technique majoritairement anglophone. Nous devons définir clairement quelle langue utiliser dans chaque contexte pour éviter la confusion et maintenir la cohérence.

## Matrice de Choix Linguistiques
| Domaine                          | Français | Anglais | Exemples                                             |
| -------------------------------- | -------- | ------- | --------------------------------------------------------- |
| **Nommage du Code**              | \[]     | \[x]    | Conventions de nommage pour variables, fonctions, classes |
| **Commentaires dans le Code**    | \[]      | \[x]     | Style et langue des commentaires techniques               |
| **Commits Git**                  | \[]      | \[x]     | Messages de commits                                       |
| **Documentation Technique**      | \[]      | \[x]     | README, documentation de référence                        |
| **Documentation Métier**         | \[x]      | \[]     | Spécifications, user stories                              |
| **Interfaces Utilisateur**       | \[]      | \[x]     | Libellés, messages, interactions                          |
| **Logs Techniques**              | \[]      | \[x]     | Messages de logs, erreurs système                         |
| **Emails Automatiques**          | \[]      | \[x]     | Communications système                                    |
| **Noms de Branches Git**         | \[]      | \[x]     | Convention de nommage des branches                        |
| **Documentation d'Architecture** | \[x]      | \[]     | ADRs, diagrammes, descriptions techniques                 |
| **Prompts IA**                   | \[x]      | \[x]     | Instructions pour les modèles de langage                  |
| **Configurations (yaml, json)**  | \[]      | \[x]     | Noms de clés, commentaires dans configs                   |
| **Tests et Assertions**          | \[]      | \[x]     | Noms de tests, messages d'assertion                       |
| **Documentation Développeur**    | \[]      | \[x]     | Guides d'onboarding, guides de contribution               |
| **Annotations et Docstrings**    | \[]      | \[x]     | Documentation inline du code                              |

## Consequences

### Avantages
- ✅ Code réutilisable et standardisé
- ✅ Accessibilité internationale
- ✅ Flexibilité linguistique
- ✅ Alignement avec les meilleures pratiques open-source

### Défis
- ❌ Overhead de gestion linguistique
- ❌ Nécessité de discipline collective
- ❌ Potentielle complexité de maintenance
