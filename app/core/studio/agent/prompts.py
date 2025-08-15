from langchain_core.messages import AIMessage

objectives_instructions = """
Tu es un extracteur de données marketing. 

MISSION : Extraire les informations d'une campagne marketing depuis une conversation client.

STRUCTURE DE SORTIE :
- objectives : "Notoriété" | "Acquisition" | "vente" | null
- media : "Display" | "Social" | "Vidéo" | null  
- context.end_target : cible démographique mentionnée | null
- context.business_context : contexte commercial mentionné | null
- context.product_context : contexte produit mentionné 

RÈGLES :
1. Utilise SEULEMENT les informations explicitement mentionnées  
2. Si information absente = null
3. Combine TOUS les messages de la conversation
4. N'invente rien, n'assume rien
5. Respecte EXACTEMENT les valeurs autorisées pour objectives/media
6. Extrait les informations en français

ANALYSE : Conversation client suivante...
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
En utilisant les informations sur le segment suivant :
{}

Génère UNIQUEMENT un prompt concis en anglais (maximum 150 mots) pour une IA de génération d'image (DALL-E, Midjourney, etc.).

Le prompt doit décrire :
- Une personne réaliste représentant ce segment
- Son apparence physique et vestimentaire
- Son environnement familial/social
- Son habitat/contexte de vie
- Style photographique réaliste

Format de réponse : SEULEMENT le prompt en anglais, sans explications ni commentaires supplémentaires.

Exemple de format attendu :
"Realistic photograph of a 35-year-old middle-class woman in casual business attire, standing with her family in front of their suburban home, natural lighting, documentary style, 4K quality"
"""


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
        
        # Gestion robuste des réponses vides ou manquantes
        try:
            if result.get('responses') and len(result['responses']) > 0:
                data = schema_class(**result['responses'][0].model_dump())
            else:
                # Créer un objet vide si aucune extraction n'est possible
                data = schema_class()
        except (IndexError, KeyError, ValueError):
            # Fallback : créer un objet vide
            data = schema_class()
            
        missing = get_missing_fields(data)
        if not missing:
            return data, messages
        clarification = f"Merci de préciser les informations suivantes : {', '.join(missing)}"
        messages.append(AIMessage(content=clarification))  # Affiche la clarification comme un message AI
        user_reply = ask_user_fn(clarification)
        messages.append(user_reply)
    raise ValueError("Impossible d'extraire toutes les informations après plusieurs tentatives.")