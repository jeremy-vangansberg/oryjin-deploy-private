from langchain_core.messages import AIMessage

objectives_instructions = """
Tu es un assistant expert chargé d'extraire les objectifs d'une campagne marketing à partir d'un brief client.

Ta mission :
- Extrais les informations clés selon la structure suivante :
  - objectives : l'objectif principal de la campagne ("Notoriété", "Acquisition", "vente")
  - media : le canal digital principal ("Display", "Social", "Vidéo")
  - context :
      - end_target : la cible démographique
      - business_context : le contexte commercial
      - product_context : le contexte produit

RÈGLES STRICTES :
- COMBINE toutes les informations mentionnées dans TOUS les messages de la conversation.
- Si une information apparaît dans un message précédent, GARDE-LA même si elle n'est pas répétée dans le dernier message.
- Utilise UNIQUEMENT les informations explicitement mentionnées dans l'ensemble des messages.
- Si une information n'est PAS clairement donnée dans AUCUN message, mets la valeur null (None en Python) pour ce champ.
- N'invente JAMAIS de valeur, même si cela te semble probable ou logique.
- Si le brief est incomplet, la sortie doit contenir des champs à null.
- Respecte strictement le format demandé (clé/valeur, pas de texte libre).
- Les valeurs possibles pour objectives : "Notoriété", "Acquisition", "vente". Pour media : "Display", "Social", "Vidéo". Mets null si aucune correspondance.
- Pour end_target, accepte toute mention de cible démographique (CSP, âge, genre, etc.) même si c'est abrégé.

IMPORTANT : Tu reçois plusieurs messages dans la conversation. Tu dois COMBINER toutes les informations de tous les messages pour créer une extraction complète et cohérente.

EXEMPLES DE RÉPONSE :

Pour une conversation avec plusieurs messages :
Message 1: "test, CSP +"
Message 2: "vidéo"
Message 3: "notoriété"

Tu dois COMBINER toutes les informations :
{
  "objectives": "Notoriété",
  "media": "Vidéo",
  "context": {
    "end_target": "CSP",
    "business_context": null,
    "product_context": null
  }
}

Pour un seul message incomplet :
{
  "objectives": null,
  "media": "Social",
  "context": {
    "end_target": null,
    "business_context": "marque de vêtements",
    "product_context": null
  }
}

Voici le brief à analyser :
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


def get_missing_fields(obj):
    """Retourne la liste des champs (y compris imbriqués) à None ou vides dans un objet Pydantic."""
    missing = []
    print(f"DEBUG - get_missing_fields - Checking object: {obj}")
    for field in obj.model_fields:
        value = getattr(obj, field, None)
        print(f"DEBUG - get_missing_fields - Field {field}: {value} (type: {type(value)})")
        if value is None or (isinstance(value, str) and value.strip() == ""):
            missing.append(field)
            print(f"DEBUG - get_missing_fields - Field {field} is missing")
        elif hasattr(value, 'model_fields'):
            sub_missing = get_missing_fields(value)
            missing.extend([f"{field}.{sub}" for sub in sub_missing])
    print(f"DEBUG - get_missing_fields - Final missing fields: {missing}")
    return missing


def clarification_loop(extractor, messages, schema_class, ask_user_fn, max_retries=3):
    """
    Boucle d'extraction structurée avec clarification utilisateur pour les champs manquants.
    - extractor : le structured_llm (ex: create_extractor(...))
    - messages : historique des messages (list)
    - schema_class : la classe Pydantic du schéma attendu
    - ask_user_fn : fonction qui pose une question à l'utilisateur et retourne un HumanMessage
    - max_retries : nombre max de tentatives
    """
    for _ in range(max_retries):
        result = extractor.invoke(messages)
        data = schema_class(**result['responses'][0].model_dump())
        missing = get_missing_fields(data)
        if not missing:
            return data, messages
        clarification = f"Merci de préciser les informations suivantes : {', '.join(missing)}"
        messages.append(AIMessage(content=clarification))  # Affiche la clarification comme un message AI
        user_reply = ask_user_fn(clarification)
        messages.append(user_reply)
    raise ValueError("Impossible d'extraire toutes les informations après plusieurs tentatives.")