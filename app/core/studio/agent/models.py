
from enum import Enum
from typing import Optional
import pandas as pd
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState

# --- Pydantic Models for State Management and Data Validation ---

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
    end_target: Optional[str] = Field(default=None, description="Cible démographique de la campagne")
    business_context: Optional[str] = Field(default=None, description="Contexte commercial de l'entreprise")
    product_context: Optional[str] = Field(default=None, description="Contexte du produit ou service")

class CampaignObjectives(BaseModel):
    """
    Extraction structurée des objectifs de campagne marketing digital.
    
    Cette classe représente les informations clés extraites d'un brief client
    pour définir une stratégie de campagne marketing digital efficace.
    """
    
    objectives: Optional[Objective] = Field(default=None, description="Objectif principal de la campagne marketing")
    media: Optional[Media] = Field(default=None, description="Canal digital principal utilisé pour la campagne")
    context: Optional[Context] = Field(default=None, description="Contexte complet de la campagne incluant cible, business et produit")
    

class Persona(BaseModel):
    """Extraction structurée des personnages marketing basés sur les statistiques des clusters."""
    cluster: int = Field(..., description="Numéro du cluster")
    FEMME: float = Field(..., description="Proportion de femmes dans le segment", ge=0, le=1)
    AGE: float = Field(..., description="Age du moyen du segment")
    PANIER_MOY: float = Field(..., description="Panier moyen du segment")
    RETAIL: float = Field(..., description="Pourcentage de vente en magasin", ge=0, le=100)
    WEB: float = Field(..., description="Pourcentage de vente en ligne", ge=0, le=100)
    RECENCE: float = Field(..., description="Recence en jours du segment")
    CSP: float = Field(..., description="Catégorie Socio-Professionnelle moyenne du segment")
    PCT_C21_MEN_FAM_CAT: float = Field(..., description="Pourcentage de ménage avec des enfants : 1->faible % avec enfant ; 4->%élévé de famille avec enfants")
    PCT_MEN_PROP_CAT: float = Field(..., description="Pourcentage de ménage propriétaire : 1->% faible  ; 5->%élévé")
    PCT_LOG_AV45_CAT: float = Field(..., description="Pourcentage de logements créés avant 1945 : 1->% faible  ; 4->%élévé")
    PCT_LOG_45_70_CAT: float = Field(..., description="Pourcentage de logements créés entre 1945 et 1970 : 1->% faible  ; 4->%élévé")
    PCT_LOG_70_90_CAT: float = Field(..., description="Pourcentage de logements créés entre 1970 et 1990 : 1->% faible  ; 4->%élévé")
    PCT_LOG_AP90_CAT: float = Field(..., description="Pourcentage de logements créés après 1990 : 1->% faible  ; 5->%élévé")
    PCT_LOG_SOC_CAT: float = Field(..., description="Pourcentage de logements sociaux : 1->% faible  ; 4->%élévé")
    REV_MED_CAT: float = Field(..., description="revenu median de la tuile ; 1->revenu faible  ; 5->revenu élévé")
    INEG_REV_CAT: float = Field(..., description="disparité de revenu dans la tuile  ; 1-> faible disparité  ; 5->forte disparité")
    ETABLISSEMENTS_CAT: float = Field(..., description="tuile contient au moins une entreprise")
    description_general: Optional[str] = Field(
        default=None, description="Personnages textuels basés sur les statistiques du segment"
    )


class Personas(BaseModel):
    """Définit l'outil pour extraire une liste de personas marketing à partir de données structurées."""
    personas: list[Persona] = Field(description="Liste des personas")


class PersonaDescriptionUpdate(BaseModel):
    """Représente la mise à jour textuelle pour un seul persona."""
    cluster: int = Field(description="Numéro du cluster à mettre à jour")
    description_general: str = Field(
        description="Description marketing détaillée du persona pour ce cluster."
    )

class PersonasUpdate(BaseModel):
    """Une liste de mises à jour de descriptions pour les personas."""
    personas: list[PersonaDescriptionUpdate]


class MyState(MessagesState):
    objectives : CampaignObjectives = None
    data : pd.DataFrame = None
    data_enriched : pd.DataFrame = None
    personas : Personas = None
    id_choice_segment : int = None
    stats_persona_summary : str = None # summary of personas stats
    image_url : str = None
    final_summary : str = None
    objectives_complete : bool = None # indique si les objectifs sont complets
    
    # Champs pour gestion stateless des interruptions
    needs_clarification : bool = None # indique si clarification nécessaire
    missing_fields : list[str] = None # champs manquants pour clarification
    awaiting_segment_selection : bool = None # indique si sélection en attente
    available_segments : int = None # nombre de segments disponibles
    segment_selection_valid : bool = None # indique si la sélection de segment est valide