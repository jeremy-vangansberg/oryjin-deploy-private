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

# Composants fonctionnels
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

## Phase 1 

## rdv 16 juin
1) Collecte des objectifs
    Message : "Je suis le directeur marketing d'un enseigne de distribution, équipement de la maison, grand public, je vends sur le web et en magasin.
             On est haut de gamme. Ma clientéle est CSP+.
             Je veux faire une campagne de recrutement de nouveaux clients sur un produit moyen gamme de façon à recruter autant sur les CSP que les CSP+. Je souhaite définir les paramètres pour ma campagne display sur Pmax de google." 
 
    Objectif : Notoriété | Acquisition | Vente 
    Media : Display | Video | Social
    Context : 
        Client :
        Business : 
    Hors POC : volume, budget, précision, média, Context : Mémoire à long terme (Facultatif)
   Voir : https://oryjin.sharepoint.com/:w:/r/_layouts/15/guestaccess.aspx?e=4%3AxdQd12&at=9&share=EVYMrN6FejBDh_QmuWzq68YBpJAqHrr_2gewpfQ-c9BRBA

2) Connexion au CRM 
   mock -> Connecteur ODBC (A chercher sur snowflake)
   Je vais vraiment faire la connexion à Snowflake mais je vise une table.
   nom_de_table = demo_seg_client
   

3) récupération des noms de table
   nom_de_table = demo_seg_client_enrichi

   CSP
   Proprietaire
   revenu moyen
   Famille


4) nombre de cluster => 4
   K-means sans rf

5) Cluster -> text
   Description du cluster par description statistique
   des données enrichies
   des données de comportement

   few shot classification.

6) HIL => Choix du segment
7) Persona => Génération 

8) Summarization et suggestion de mapping 


Demo
   

Personna textuel (exemple) : 
Age moyen : 34
Situation familiale : Marié
Revenu moyen ( ) : élevé
Panier moyen : élevé
CSP : CSP+
Canal d'achat : Internet
Zone d'habitation : Rurale
Type d'habitation : Pavillon

=> Persona 
    => résumé textuel
    => visuel
    => résumé descriptif



https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about