import operator
from pydantic import BaseModel, Field
from langgraph.graph import END, MessagesState, START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_mistralai import ChatMistralAI
from IPython.display import Image, display
import pandas as pd
from trustcall import create_extractor

from utils import get_cursor, get_table
from dotenv import load_dotenv


load_dotenv()

llm = ChatMistralAI(model="mistral-medium-latest", temperature=0)

from pydantic import BaseModel, Field
from enum import Enum

class Objective(str, Enum):
    awareness = "Notoriété"
    acquisition = "Acquisition"
    sales = "vente"

    def __str__(self):
        return self.value

class Media(str, Enum):
    display = "Display"
    video = "Vidéo"
    social = "Social"

    def __str__(self):
        return self.value

class Context(BaseModel):
    """Contexte détaillé d'une campagne marketing incluant cible, business et produit."""
    
    end_target: str = Field(
        description="Cible démographique de la campagne",
        examples=["CSP+", "CSP+ et CSP (élargissement)", "jeunes 18-25 ans"]
    )
    business_context: str = Field(
        description="Contexte commercial de l'entreprise",
        examples=["Distribution équipement maison, haut de gamme, vente web + magasin"]
    )
    product_context: str = Field(
        description="Contexte du produit ou service",
        examples=["Produit moyen gamme (nouveau)", "Équipement maison haut de gamme"]
    )

class CampaignObjectives(BaseModel):
    """
    Extraction structurée des objectifs de campagne marketing digital.
    
    Cette classe représente les informations clés extraites d'un brief client
    pour définir une stratégie de campagne marketing digital efficace.
    """
    
    objectives: Objective = Field(
        description="Objectif principal de la campagne marketing"
    )
    media: Media = Field(
        description="Canal digital principal utilisé pour la campagne"
    ) 
    context: Context = Field(
        description="Contexte complet de la campagne incluant cible, business et produit")
    
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

class MyState(MessagesState):
    objectives : CampaignObjectives = None
    # data : pd.DataFrame = None


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
    cursor = get_cursor()
    data = get_table(table_name="DEMO_SEG_CLIENT")
    data_preview = f"""📊 Données client collectées avec succès !
🔍 Aperçu des premières lignes :
{data.head(5).to_string(max_cols=10, max_colwidth=20)}
"""
    return {    
        "data": data,
        "messages": state["messages"] + [AIMessage(content=data_preview)]
    }

def enrich_data(state: MyState):
    cursor = get_cursor()
    data = get_table(table_name="DEMO_SEG_CLIENT_ENRICHI")
    data_preview = f"""📊 Données client collectées avec succès !
    🔍 Aperçu des premières lignes :
    {data.head(5).to_string(max_cols=10, max_colwidth=20)}
    """
    return {    
        "data": data,
        "messages": state["messages"] + [AIMessage(content=data_preview)]
        }

def perform_clustering(state: MyState):
    pass

def generate_textual_personas(state: MyState):
    pass

def select_customer_segment(state: MyState):
    pass

def generate_visual_personas(state: MyState):
    pass 

def summarize_dsp_mappings(state: MyState):
    pass


dsp = StateGraph(MyState)
dsp.add_node("collect_campaign_objectives", collect_campaign_objectives)
dsp.add_node("collect_data", collect_data)
dsp.add_node("enrich data", enrich_data)  
# dsp.add_node("perform clustering", perform_clustering)
# dsp.add_node("generate textual personas", generate_textual_personas)
# dsp.add_node("select customer segment", select_customer_segment)
# dsp.add_node("generate visual personas", generate_visual_personas)
# dsp.add_node("mapping suggestions", summarize_dsp_mappings)


dsp.add_edge(START, "collect_campaign_objectives")
dsp.add_edge("collect_campaign_objectives", "collect_data")
dsp.add_edge("collect_data", "enrich data")
# dsp.add_edge("enrich data", "perform clustering")
# dsp.add_edge("perform clustering", "generate textual personas")
# dsp.add_edge("generate textual personas", "select customer segment")
# dsp.add_edge("select customer segment", "generate visual personas")
# dsp.add_edge("generate visual personas", "mapping suggestions")


dsp.add_edge("enrich data", END)

graph = dsp.compile()
# View
display(Image(graph.get_graph().draw_mermaid_png()))