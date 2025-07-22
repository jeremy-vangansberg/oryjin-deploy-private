"""
Main entry point for the Oryjin marketing campaign assistant agent.

This script defines a multi-step conversational agent using LangGraph. The agent guides the user
through defining a marketing campaign, from setting objectives to generating visual personas
for targeted customer segments.

The agent's flow is structured as a state machine, where each step (node) performs a specific
task, such as collecting data, running clustering, or interacting with an LLM to generate content.
"""
from dotenv import load_dotenv
from agent.image import generate_and_upload_image
from IPython.display import Image, display
from langchain_core.messages import AIMessage, SystemMessage
from langchain_mistralai import ChatMistralAI
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from agent.prompts import objectives_instructions, viz_persona, clustering_instructions

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

def collect_campaign_objectives(state: MyState):
    message = state["messages"][0]
    structured_llm = create_extractor(llm, tools=[CampaignObjectives], tool_choice="CampaignObjectives")
    # structured_llm = llm.with_structured_output(CampaignObjectives)
    campaign_objectives =structured_llm.invoke([
        SystemMessage(content=objectives_instructions),
        message
        ])
    campaign_objectives = CampaignObjectives(**campaign_objectives['responses'][0].model_dump())

    print(campaign_objectives)

    objectives_summary = f"""
    ✅ Objectifs de campagne collectés :

    Objectif : {campaign_objectives.objectives}
    Média : {campaign_objectives.media}
    Contexte :
    - Cible : {campaign_objectives.context.end_target}
    - Business : {campaign_objectives.context.business_context}
    - Produit : {campaign_objectives.context.product_context}
    """

    return {
        "objectives": campaign_objectives,
        "messages": state["messages"] + [AIMessage(content=objectives_summary)]
    }

def collect_data(state: MyState):
    data = get_table(table_name="DEMO_SEG_CLIENT")
    # data_preview = f"""📊 Données client collectées avec succès !
    # 🔍 Aperçu des premières lignes :
    # {data.head(5).to_string(max_cols=10, max_colwidth=20)}
    # """

    data_preview = "📊 Données client collectées avec succès !"

    return {    
        "data": data,
        "messages": state["messages"] + [AIMessage(content=data_preview)]
    }

def enrich_data(state: MyState):
    data_enriched = get_table(table_name="DEMO_SEG_CLIENT_ENRICHI_CAT")
    # data_preview = f"""📊 Données client enrichies avec succès !
    # 🔍 Aperçu des premières lignes :
    # {data_enriched.head(5).to_string(max_cols=15, max_colwidth=20)}
    # """

    data_preview = "📊 Données client enrichies avec succès !"

    return {    
        "data_enriched": data_enriched,
        "messages": state["messages"] + [AIMessage(content=data_preview)]
        }

def perform_clustering(state: MyState):
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
    personas_data = response['responses'][0].model_dump()['personas']
    personas = Personas(personas=[Persona(**p) for p in personas_data])

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
    # 1. Récupérer l'objet Personas existant du state
    personas_stats_summary = state["stats_persona_summary"]
    existing_personas = state["personas"]

    prompt_content = f"""
    Tu es un expert en marketing digital et en segmentation client.

    Mission : Pour chaque cluster décrit ci-dessous, rédige une description marketing détaillée et vivante.

    Format de sortie : Ta réponse doit être une liste d'objets. Chaque objet doit contenir IMPÉRATIVEMENT les champs "cluster" (le numéro du segment) et "description_general" (le texte du persona).

    Voici les statistiques des {N_CLUSTERS} clusters :
    {personas_stats_summary}
    """

    # 2. Définir un extracteur avec un schéma de sortie simple et précis
    structured_llm = create_extractor(llm, tools=[PersonasUpdate], tool_choice="PersonasUpdate")
    
    response = structured_llm.invoke([
        SystemMessage(content=prompt_content),
    ])
    
    # 3. Valider la sortie du LLM
    updates = PersonasUpdate(**response['responses'][0].model_dump())
    descriptions_map = {update.cluster: update.description_general for update in updates.personas}

    # 4. Mettre à jour l'objet "Personas" existant (approche mutable)
    for persona in existing_personas.personas:
        if persona.cluster in descriptions_map:
            persona.description_general = descriptions_map[persona.cluster]

    # 5. Générer le résumé pour l'affichage
    textual_personas_summary = '\n'.join([
        f"🎯 Segment {p.cluster}:\n{p.description_general}"
        for p in existing_personas.personas
    ])

    textual_personas_preview = f"""📊 Personnages textuels générés :\n{textual_personas_summary}"""

    # 6. Retourner l'objet Personas qui a été modifié
    return {
        "personas": existing_personas,
        "textual_persona_summary": textual_personas_summary,
        "messages": state["messages"] + [AIMessage(content=textual_personas_preview)]
    }


def select_customer_segment(state: MyState):
    """
    Reads the user's segment choice from the state after the graph resumes,
    and returns a confirmation message to be added to the chat.
    """
    print("Waiting for user input...")
    id_segment = interrupt(value="Ready for user input.")

    id_segment = int(id_segment)

    # This check is important for when the graph resumes
    if id_segment is None:
        # This can happen if the UI doesn't correctly update the state.
        # We add an error message to the chat to make it visible.
        return {"messages": state["messages"] + [AIMessage(content="Erreur: Aucun segment n'a été sélectionné. Le processus ne peut pas continuer.")]}

    personas = state["personas"]
    # Ensure the selected ID is valid
    if id_segment >= len(personas.personas):
        return {"messages": state["messages"] + [AIMessage(content=f"Erreur: L'ID de segment {id_segment} est invalide.")]}
        
    persona = personas.personas[id_segment]
    
    print(f"Segment choisi par l'utilisateur : {persona.cluster}")
    
    confirmation_message = f"Vous avez choisi le segment {persona.cluster}. Le processus continue..."
    
    # Return a dictionary to update the state. This is the correct way to proceed.
    return {
        "id_choice_segment": id_segment,
        "messages": state["messages"] + [AIMessage(content=confirmation_message)]
    }
    

def generate_visual_persona(state: MyState):
    id_segment = state["id_choice_segment"]
    personas = state["personas"]
    persona = personas.personas[id_segment]
    persona_description = persona.description_general
    response = llm.invoke([SystemMessage(content=viz_persona.format(persona_description))])

    # La réponse de llm.invoke est un objet AIMessage, on accède à son contenu avec .content
    visual_persona_prompt = response.content
    image_url = generate_and_upload_image(visual_persona_prompt, "images-oryjin", "config_gcloud.json", folder="personas")

    return {
        "image_url": image_url,
        "messages": state["messages"] + [AIMessage(content=
        f"""prompt utilisée : {visual_persona_prompt}\n
        ---\n
        Persona description :
        {persona_description}
        ---\n
        Image générée pour le persona {image_url}"""
        )]
    }


def summarize_dsp_mappings(state: MyState):
    pass


dsp = StateGraph(MyState)
dsp.add_node("collect campaign objectives", collect_campaign_objectives)
dsp.add_node("collect data", collect_data)
dsp.add_node("enrich data", enrich_data)  
dsp.add_node("perform clustering", perform_clustering)
dsp.add_node("generate textual personas", generate_textual_personas)
dsp.add_node("select customer segment", select_customer_segment)
dsp.add_node("generate visual persona", generate_visual_persona)
# dsp.add_node("mapping suggestions", summarize_dsp_mappings)


dsp.add_edge(START, "collect campaign objectives")
dsp.add_edge("collect campaign objectives", "collect data")
dsp.add_edge("collect data", "enrich data")
dsp.add_edge("enrich data", "perform clustering")
dsp.add_edge("perform clustering", "generate textual personas")
dsp.add_edge("generate textual personas", "select customer segment")
dsp.add_edge("select customer segment", "generate visual persona")
dsp.add_edge("generate visual persona", END)

# graph = dsp.compile(interrupt_before=["select customer segment"])
graph = dsp.compile()
# View
display(Image(graph.get_graph().draw_mermaid_png()))

