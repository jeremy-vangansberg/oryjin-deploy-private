"""
Main entry point for the Oryjin marketing campaign assistant agent.

This script defines a multi-step conversational agent using LangGraph. The agent guides the user
through defining a marketing campaign, from setting objectives to generating visual personas
for targeted customer segments.

The agent's flow is structured as a state machine, where each step (node) performs a specific
task, such as collecting data, running clustering, or interacting with an LLM to generate content.

ARCHITECTURE: STATELESS MICRO-SERVICES
- Nodes are pure functions without side-effects (no interrupt() calls)
- Interruptions are managed externally via API/Studio configuration
- State is prepared by nodes, interruptions decided by orchestrator
- Persistence is handled automatically by LangGraph API (no custom checkpointer needed)
- Two patterns for user interaction:
  * OBJECTIFS: validate → check_completion → {complete: continue | incomplete: await_clarification}
  * SEGMENTS: validate → check_need_input → {valid: continue | invalid/missing: await_selection}
- Conditional edges on validation nodes determine if user input is needed

USAGE WITH API:
  config = {
    "interrupt_before": ["await_user_clarification", "await_segment_selection"]
  }
  client.start_run(thread_id, "campaign-assistant", input_data, config=config)
"""
from dotenv import load_dotenv
import os
from agent.image import generate_and_upload_image
from IPython.display import Image, display
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_mistralai import ChatMistralAI
from langgraph.graph import END, START, StateGraph
from agent.prompts import objectives_instructions, viz_persona, clustering_instructions, clarification_loop
from agent.prompts import get_missing_fields
from trustcall import create_extractor
from agent.utils import get_table
from agent.clustering import perform_kmeans
from agent.models import CampaignObjectives, Personas, PersonasUpdate, Persona, MyState 


# --- Constants and Global Configurations ---
load_dotenv()

# Defines the number of customer segments to generate.
N_CLUSTERS = 4

# Initialize the language model for all generative tasks.
llm = ChatMistralAI(model="mistral-medium-latest", temperature=0)

def extract_text_from_content(content):
    """Extrait le texte d'un contenu de message, qu'il soit string ou liste"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and 'text' in item:
                text_parts.append(item['text'])
            elif isinstance(item, str):
                text_parts.append(item)
        return ' '.join(text_parts)
    else:
        return str(content)

def collect_campaign_objectives(state: MyState):
    """Collecte et met à jour les objectifs de campagne"""
    messages = state["messages"]
    
    # Créer l'extractor avec enable_inserts=True pour les updates
    structured_llm = create_extractor(
        llm, 
        tools=[CampaignObjectives], 
        tool_choice="CampaignObjectives",
        enable_inserts=True
    )
    
    print(f"DEBUG - Traitement de {len(messages)} messages")
    
    # Préparer les données existantes si on en a
    existing_data = []
    if state.get("objectives"):
        existing_objectives = state["objectives"]
        existing_data = [("0", "CampaignObjectives", existing_objectives.model_dump())]
        print(f"DEBUG - Mise à jour des données existantes")
    
    # Construire le message de conversation
    conversation_parts = []
    for msg in messages:
        if hasattr(msg, 'content'):
            text = extract_text_from_content(msg.content)
            conversation_parts.append(text)
    
    conversation = "\n".join(conversation_parts)
    
    # Invoquer avec les données existantes
    result = structured_llm.invoke({
        "messages": [
            SystemMessage(content=objectives_instructions),
            HumanMessage(content=f"Extrais et mets à jour les objectifs de campagne basés sur cette conversation:\n\n{conversation}")
        ],
        "existing": existing_data
    })
    
    # Gestion robuste des réponses vides ou manquantes
    try:
        if result.get('responses') and len(result['responses']) > 0:
            campaign_objectives = CampaignObjectives(**result['responses'][0].model_dump())
            print(f"DEBUG - Objectifs extraits: {campaign_objectives}")
        else:
            # Créer un objet vide si aucune extraction n'est possible
            print("DEBUG - Aucun objectif extrait, création d'un objet vide")
            campaign_objectives = CampaignObjectives()
    except (IndexError, KeyError, ValueError) as e:
        print(f"DEBUG - Erreur extraction objectifs: {e}")
        # Fallback : créer un objet vide
        campaign_objectives = CampaignObjectives()
    
    return {
        "objectives": campaign_objectives,
        "messages": state["messages"]
    }

def validate_campaign_objectives(state: MyState):
    """Valide les objectifs et interrompt si des informations manquent"""
    objectives = state["objectives"]
    missing = get_missing_fields(objectives)
    
    print(f"DEBUG - Validation - Champs manquants: {missing}")
    
    if missing:
        # Préparer le message de clarification
        objectives_summary = f"""
        ✅ Objectifs de campagne extraits (partiels) :

        Objectif : {objectives.objectives}
        Média : {objectives.media}
        Contexte :
        - Cible : {objectives.context.end_target if objectives.context else None}
        - Business : {objectives.context.business_context if objectives.context else None}
        - Produit : {objectives.context.product_context if objectives.context else None}
        """
        clarification = f"Merci de préciser les informations suivantes : {', '.join(missing)}"
        ai_message = AIMessage(content=objectives_summary + '\n' + clarification)
        
        # Ajouter le message et marquer comme incomplet
        return {
            **state, 
            "messages": state["messages"] + [ai_message],
            "objectives_complete": False
        }
    else:
        # Objectifs complets, continuer
        objectives_summary = f"""
        ✅ Objectifs de campagne collectés :

        Objectif : {objectives.objectives}
        Média : {objectives.media}
        Contexte :
        - Cible : {objectives.context.end_target if objectives.context else None}
        - Business : {objectives.context.business_context if objectives.context else None}
        - Produit : {objectives.context.product_context if objectives.context else None}
        """
        ai_message = AIMessage(content=objectives_summary)
        return {
            **state, 
            "messages": state["messages"] + [ai_message],
            "objectives_complete": True
        }

def check_objectives_completion(state: MyState):
    """Conditional edge : continue si objectifs complets, sinon attendre feedback"""
    if state.get("objectives_complete", False):
        return "collect data"
    else:
        return "await_user_clarification"

def await_user_clarification(state: MyState):
    """Node pur qui prépare l'état pour attendre la clarification utilisateur"""
    pass

def collect_data(state: MyState):
    """Collecte les données client de base"""
    data = get_table(table_name="DEMO_SEG_CLIENT")
    data_preview = "📊 Données client collectées avec succès !"

    return {    
        "data": data,
        "messages": state["messages"] + [AIMessage(content=data_preview)]
    }

def enrich_data(state: MyState):
    """Enrichit les données client avec des informations catégorielles"""
    data_enriched = get_table(table_name="DEMO_SEG_CLIENT_ENRICHI_CAT")
    data_preview = "📊 Données client enrichies avec succès !"

    return {    
        "data_enriched": data_enriched,
        "messages": state["messages"] + [AIMessage(content=data_preview)]
    }

def perform_clustering(state: MyState):
    """Effectue le clustering k-means et génère les personas statistiques"""
    data = state["data_enriched"]
    statistics_clusters_preview = perform_kmeans(data)

    structured_llm = create_extractor(llm, tools=[Personas], tool_choice="Personas")

    prompt_unifie = f"""
{clustering_instructions}

Voici les données JSON à traiter :
```json
{statistics_clusters_preview}
```
"""
    
    response = structured_llm.invoke([SystemMessage(content=prompt_unifie)])
    
    # Gestion robuste des réponses vides ou manquantes
    try:
        if response.get('responses') and len(response['responses']) > 0:
            personas_data = response['responses'][0].model_dump()['personas']
            personas = Personas(personas=[Persona(**p) for p in personas_data])
            print(f"DEBUG - Personas extraites du clustering: {len(personas_data)} personas")
        else:
            print("DEBUG - Aucune persona extraite du clustering, création d'une liste vide")
            personas = Personas(personas=[])
    except (IndexError, KeyError, ValueError) as e:
        print(f"DEBUG - Erreur extraction personas clustering: {e}")
        # Fallback : créer un objet vide
        personas = Personas(personas=[])

    # Formater les clusters pour l'affichage
    clusters_formatted = '\n'.join([
    f"""
    🎯 Segment {persona.cluster}:
    • Genre: {persona.FEMME:.0%} femmes
    • Âge: {persona.AGE:.0f} ans
    • Panier: {persona.PANIER_MOY:.0f}€
    • Canal: {persona.RETAIL:.0f}% retail / {persona.WEB:.0f}% web
    • Récence: {persona.RECENCE:.0f} jours
    
    🏡 Habitat & Famille:
    • Propriétaires: {persona.PCT_MEN_PROP_CAT:.1f}%
    • Familles avec enfants: {persona.PCT_C21_MEN_FAM_CAT:.1f}%
    • Logements sociaux: {persona.PCT_LOG_SOC_CAT:.1f}%
    • Ancienneté du logement (score):
        - Avant 1945: {persona.PCT_LOG_AV45_CAT:.1f}%
        - 1945-1970: {persona.PCT_LOG_45_70_CAT:.1f}%
        - 1970-1990: {persona.PCT_LOG_70_90_CAT:.1f}%
        - Après 1990: {persona.PCT_LOG_AP90_CAT:.1f}%

    💼 Revenus & CSP:
    • Revenu médian: {persona.REV_MED_CAT:.1f}/5
    • Disparité revenus: {persona.INEG_REV_CAT:.1f}/5
    • CSP (moyenne): {persona.CSP:.1f}/5
    
    🏢 Environnement:
    • Présence d'entreprises: {persona.ETABLISSEMENTS_CAT:.1f}%
    """
    for persona in personas.personas
])

    statistics_clusters_preview = f"""
    📊 Statistiques des clusters :
   {clusters_formatted}
    """

    return {
        "personas": personas,
        "stats_persona_summary": statistics_clusters_preview,
        "messages": state["messages"] + [AIMessage(content=statistics_clusters_preview)]
    }

def generate_textual_personas(state: MyState):
    """Génère les descriptions textuelles des personas marketing"""
    personas_stats_summary = state["stats_persona_summary"]
    existing_personas = state["personas"]

    prompt_content = f"""
    Tu es un expert en marketing digital et en segmentation client.

    Mission : Pour chaque cluster décrit ci-dessous, rédige une description marketing détaillée et vivante.

    Format de sortie : Ta réponse doit être une liste d'objets. Chaque objet doit contenir IMPÉRATIVEMENT les champs "cluster" (le numéro du segment) et "description_general" (le texte du persona).

    Voici les statistiques des {N_CLUSTERS} clusters :
    {personas_stats_summary}
    """

    structured_llm = create_extractor(llm, tools=[PersonasUpdate], tool_choice="PersonasUpdate")
    
    response = structured_llm.invoke([
        SystemMessage(content=prompt_content),
    ])
    
    # Gestion robuste des réponses vides ou manquantes
    try:
        if response.get('responses') and len(response['responses']) > 0:
            updates = PersonasUpdate(**response['responses'][0].model_dump())
            descriptions_map = {update.cluster: update.description_general for update in updates.personas}
            print(f"DEBUG - Descriptions textuelles extraites: {len(updates.personas)} personas")
        else:
            print("DEBUG - Aucune description textuelle extraite, utilisation d'un dict vide")
            descriptions_map = {}
    except (IndexError, KeyError, ValueError) as e:
        print(f"DEBUG - Erreur extraction descriptions textuelles: {e}")
        # Fallback : dict vide
        descriptions_map = {}

    # Mettre à jour l'objet Personas existant
    for persona in existing_personas.personas:
        if persona.cluster in descriptions_map:
            persona.description_general = descriptions_map[persona.cluster]

    # Générer le résumé pour l'affichage
    textual_personas_summary = '\n'.join([
        f"🎯 Segment {p.cluster}:\n{p.description_general}"
        for p in existing_personas.personas
    ])

    textual_personas_preview = f"""📊 Personnages textuels générés :\n{textual_personas_summary}"""

    return {
        "personas": existing_personas,
        "textual_persona_summary": textual_personas_summary,
        "messages": state["messages"] + [AIMessage(content=textual_personas_preview)]
    }

def await_segment_selection(state: MyState):
    """Node pur qui prépare l'état pour attendre la sélection de segment"""
    # Node placeholder - l'interruption est gérée par l'API externe
    return state

def validate_segment_selection(state: MyState):
    """Valide la sélection de segment et gère les erreurs"""
    messages = state["messages"]
    personas = state["personas"]
    
    # Vérifier s'il y a un choix de segment dans le state ou le dernier message
    id_segment = state.get("id_choice_segment")
    
    # Si pas d'ID dans le state, essayer d'extraire du dernier message utilisateur
    if id_segment is None and len(messages) > 0:
        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            try:
                content = str(last_message.content).strip()
                id_segment = int(content)
                print(f"DEBUG - Segment extrait du message: {id_segment}")
            except (ValueError, AttributeError):
                print("DEBUG - Impossible d'extraire le segment du message")
                id_segment = None
    
    # Si toujours pas d'ID, c'est la première fois → demander à l'utilisateur
    if id_segment is None:
        print("DEBUG - Aucun segment sélectionné, demande de sélection")
        
        # Préparer le message de sélection
        selection_message = "Veuillez choisir un segment pour générer le persona visuel :\n\n"
        for i, persona in enumerate(personas.personas):
            selection_message += f"🎯 **Segment {i}** : {persona.description_general[:100]}...\n\n"
        
        selection_message += "Entrez le numéro du segment choisi (0, 1, 2, etc.)"
        
        ai_message = AIMessage(content=selection_message)
        
        return {
            **state,
            "messages": state["messages"] + [ai_message],
            "segment_selection_valid": False
        }
    
    # Valider l'ID du segment
    try:
        if id_segment < 0 or id_segment >= len(personas.personas):
            print(f"DEBUG - Segment invalide: {id_segment}")
            error_message = f"Erreur: L'ID de segment '{id_segment}' est invalide. Choisissez entre 0 et {len(personas.personas)-1}."
            
            return {
                **state,
                "messages": state["messages"] + [AIMessage(content=error_message)],
                "segment_selection_valid": False,
                "id_choice_segment": None  # Reset pour forcer une nouvelle sélection
            }
        
        # Segment valide
        persona = personas.personas[id_segment]
        print(f"DEBUG - Segment valide choisi: {persona.cluster}")
        
        confirmation_message = f"✅ Vous avez choisi le segment {id_segment}. Génération du persona visuel en cours..."
        
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=confirmation_message)],
            "id_choice_segment": id_segment,
            "segment_selection_valid": True
        }
        
    except Exception as e:
        print(f"DEBUG - Erreur validation segment: {e}")
        error_message = "Erreur: Format invalide. Veuillez entrer un numéro de segment valide (0, 1, 2, etc.)"
        
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=error_message)],
            "segment_selection_valid": False,
            "id_choice_segment": None
        }

def check_segment_need_input(state: MyState):
    """Conditional edge : vérifie si on a besoin d'input utilisateur ou si on peut continuer"""
    segment_valid = state.get("segment_selection_valid", False)
    
    if segment_valid:
        # Segment valide → continuer vers génération
        print("DEBUG - Segment valide, continuer vers génération")
        return "generate visual persona"
    else:
        # Pas de segment ou segment invalide → attendre input utilisateur
        print("DEBUG - Besoin d'input utilisateur pour le segment")
        return "await segment selection"

def generate_visual_persona(state: MyState):
    """Génère et upload l'image du persona sélectionné"""
    id_segment = state["id_choice_segment"]
    personas = state["personas"]
    persona = personas.personas[id_segment]
    persona_description = persona.description_general
    
    response = llm.invoke([SystemMessage(content=viz_persona.format(persona_description))])
    visual_persona_prompt = response.content
    
    # Créer l'uploader Azure
    from agent.image import AzureBlobUploader

    AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
    AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
    
    uploader = AzureBlobUploader(AZURE_CONNECTION_STRING, AZURE_CONTAINER_NAME)
    image_url = generate_and_upload_image(visual_persona_prompt, uploader, folder="personas")

    return {
        "image_url": image_url,
        "messages": state["messages"] + [AIMessage(content=
        f"""🎨 Persona visuel généré avec succès !

**Prompt utilisé :** {visual_persona_prompt}

**Description du persona :**
{persona_description}

**Image générée :** {image_url}"""
        )]
    }

# --- Graph Construction ---

dsp = StateGraph(MyState)

# Ajouter les nœuds
dsp.add_node("collect campaign objectives", collect_campaign_objectives)
dsp.add_node("validate campaign objectives", validate_campaign_objectives)
dsp.add_node("await_user_clarification", await_user_clarification)
dsp.add_node("collect data", collect_data)
dsp.add_node("enrich data", enrich_data)  
dsp.add_node("perform clustering", perform_clustering)
dsp.add_node("generate textual personas", generate_textual_personas)
dsp.add_node("await segment selection", await_segment_selection)
dsp.add_node("validate segment selection", validate_segment_selection)
dsp.add_node("generate visual persona", generate_visual_persona)

# Définir les edges - Flow avec boucle de clarification
dsp.add_edge(START, "collect campaign objectives")
dsp.add_edge("collect campaign objectives", "validate campaign objectives")
dsp.add_conditional_edges("validate campaign objectives", check_objectives_completion, 
                         ["collect data", "await_user_clarification"])
dsp.add_edge("await_user_clarification", "collect campaign objectives")  # Reboucler après clarification
dsp.add_edge("collect data", "enrich data")
dsp.add_edge("enrich data", "perform clustering")
dsp.add_edge("perform clustering", "generate textual personas")
dsp.add_edge("generate textual personas", "validate segment selection")
dsp.add_conditional_edges("validate segment selection", check_segment_need_input,
                         ["generate visual persona", "await segment selection"])
dsp.add_edge("await segment selection", "validate segment selection")  # Après attente → revalidation
dsp.add_edge("generate visual persona", END)

# Compilation STATELESS - Les interruptions sont gérées par l'orchestrateur/API
# La persistence est gérée automatiquement par LangGraph API
# Points d'interruption recommandés via API/Studio :
# - interrupt_before: ["await_user_clarification"] pour clarifications d'objectifs
# - interrupt_before: ["await_segment_selection"] pour sélection de segment
# LOGIC: Conditional edges sur les nodes de validation pour déterminer si input utilisateur nécessaire
graph = dsp.compile()

# View
display(Image(graph.get_graph().draw_mermaid_png()))
