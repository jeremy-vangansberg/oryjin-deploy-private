objectives_instructions = """
Analyse ce brief de campagne marketing et extrais les informations clés selon la structure demandée.

LOGIQUE D'EXTRACTION DES OBJECTIFS :
• "Acquisition" si le brief mentionne : recruter, nouveaux clients, élargir cible, leads, prospects, acquisition
• "Notoriété" si le brief mentionne : faire connaître, visibilité, awareness, image de marque, branding
• "vente" si le brief mentionne : ventes directes, chiffre d'affaires, conversions, ROI, performance

LOGIQUE D'EXTRACTION DES MÉDIAS :
• "Display" si mention de : bannières, programmatique, Google Ads Display, DSP, retargeting, display
• "Social" si mention de : Facebook, Instagram, LinkedIn, TikTok, réseaux sociaux, social media
• "Vidéo" si mention de : YouTube, vidéo display, campagnes vidéo, pre-roll, video ads

LOGIQUE D'EXTRACTION DU CONTEXTE :
• end_target : Extraire la cible précise mentionnée (CSP+, CSP, âge, etc.) + noter si élargissement
• business_context : Secteur + positionnement + canaux de vente + type d'entreprise
• product_context : Type produit + gamme prix + statut (nouveau/existant) + spécificités

EXEMPLES DE MAPPING :
"recruter nouveaux clients CSP avec du display" → Acquisition + Display + cible CSP
"faire connaître notre marque sur Instagram" → Notoriété + Social + branding
"booster les ventes via campagne YouTube" → vente + Vidéo + performance

RÈGLES :
- Utilise uniquement les informations explicitement mentionnées dans le brief
- Sois précis et factuel, n'invente pas d'informations
- Si une information est ambiguë, choisis l'interprétation la plus probable
- Priorise les termes exacts utilisés par le client

Analyse maintenant le brief suivant :
"""


clustering_instructions = """
Votre mission est de transformer des données de clustering en personas marketing complets.

La structure de votre réponse DOIT être un unique objet JSON avec une clé "personas". La valeur de cette clé doit être une liste d'objets, où chaque objet représente un persona.

Voici un exemple de la structure EXACTE que vous devez produire :
```json
{
  "personas": [
    {
      "cluster": 0,
      "FEMME": 0.51,
      "AGE": 54,
      "PANIER_MOY": 120,
      "RETAIL": 70,
      "WEB": 30,
      "RECENCE": 90,
      "CSP": 3,
      "PCT_C21_MEN_FAM_CAT": 2,
      "PCT_MEN_PROP_CAT": 4,
      "PCT_LOG_AV45_CAT": 1,
      "PCT_LOG_45_70_CAT": 3,
      "PCT_LOG_70_90_CAT": 4,
      "PCT_LOG_AP90_CAT": 2,
      "PCT_LOG_SOC_CAT": 1,
      "REV_MED_CAT": 4,
      "INEG_REV_CAT": 3,
      "ETABLISSEMENTS_CAT": 1,
      "description_general": "Description générale du persona...",
    }
  ]
}
```

Pour chaque cluster dans les données d'entrée que vous recevrez :
1.  **COPIER-COLLER LES DONNÉES** : D'abord, recopiez TOUTES les clés et valeurs numériques du cluster.
2.  **CRÉER LE CONTENU MARKETING** : Ensuite, ajoutez les champs `name`, `description_general`, `description_display`, et `description_sea`.

Votre réponse finale doit être UNIQUEMENT cet objet JSON.
"""


persona_informations = 'placeholder'

viz_persona = """
En utilisant les informations sur le segments suivants :
{}

Crée un prompt qui permet d'avoir une incarnation du persona afin de faire une représentation visuelle actionnable
pour un segment marketing. On veut que le visuel soit réaliste. Il doit représenter une personne, sa famille,
son habitat, son CSP, etc.

Exemple : 

Agit en tant que graphiste. 
Je suis un consultant marketing spécialisé dans l'analyse des consommateurs. 
Je veux créer un visuel de type photographie réaliste représentant un client type. 
Réalise un visuel de ce type représentant : un jeune couple la trentaine, avec un jeune enfant de 2 ans, de revenue modeste, pris en photo devant leur petit pavillon en zone périurbaine. 
La photo est prise en fin d'après-midi. 
On devine un voisinage avec des maisons de même style """