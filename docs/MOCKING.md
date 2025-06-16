# Composants mockés — Phase 1 (x : phase 1, o : phase 2)

| Composant | Description | Mocké | Réel |
|------------|-------------|-------|------|
| Collection objectif campagne | Génération de contenu structuré | [x] | [ ] |
| Connexion CRM | Accès aux données clients (API sécurisée) | [x] | [ ] |
| Traitement des données CRM* | Agrégation, enrichissement, préparation segmentation | [x] | [] |
| Algorithme de segmentation ML | Modèle de clustering ou scoring** | [x] | [] |
| Génération des visualisations de segmentation | Graphiques et tableaux croisés | [x] | [ ] |
| Génération de Persona (descriptif texte) | Génération automatique de profils cibles | [x] | [ ] |
| Génération de visuels Persona | Images IA des cibles et habitats | [] | [x] |
| Mapping DSP | Transformation des critères pour la DSP | [] | [x] |
| Connexion API DSP | Transmission des instructions de ciblage | [] | [ ] |
| Génération de briefing DSP | Production des briefs détaillés | [] | [ ] |
| Gestion des consentements utilisateurs | Journalisation des validations | [] | [ ] |
| Génération de prompts métiers | Première bibliothèque de prompts | [ ] | [x] |


Objectif de campagne
Type de campagne : prospection, branding,
Destination



1) Node: Collecte des objectifs
2) Node: Connexion au CRM (mock\*)
3) Node: Enrichissement (mock\*)
4) Node : K-means (simplifié)
5) Node : Clusters-to-text -> personna textuel du segment
6) Node : Personna_txt-to_Personna_viz (possibilité d'inversé)
7) Node : HIL => Sélection d'un personna (1 seul)
8) Node : summarization
9) Node : En instruction DSP (3-5 variables à extraire)


\* Par Oryjin
\*\* K-means