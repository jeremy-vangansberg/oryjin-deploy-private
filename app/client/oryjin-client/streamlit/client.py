import streamlit as st
import requests
import json
from typing import Dict, Any, Optional
import sseclient
from datetime import datetime

LANGGRAPH_API_URL = "https://ht-nautical-decoration-70-7d3b580d2cc25c4fb59221f2145e155e.us.langgraph.app"
API_KEY = "***REMOVED***"
ASSISTANT_ID = "fe096781-5601-53d2-b2f6-0d3403f7e9ca"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}


class LangGraphClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
    
    def create_thread(self) -> str:
        """Créer un nouveau thread"""
        response = requests.post(
            f"{self.base_url}/threads",
            headers=self.headers,
            json={}
        )
        response.raise_for_status()
        return response.json()["thread_id"]
    
    def stream_run(self, thread_id: str, assistant_id: str, 
                   input_data: Optional[Dict[str, Any]] = None,
                   interrupt_before: Optional[list] = None,
                   interrupt_after: Optional[list] = None) -> sseclient.SSEClient:
        """
        Stream un run avec gestion des interruptions
        
        Args:
            thread_id: ID du thread
            assistant_id: ID de l'assistant
            input_data: Données d'entrée (pour le premier appel ou après interruption)
            interrupt_before: Liste des nodes où interrompre avant exécution
            interrupt_after: Liste des nodes où interrompre après exécution
        """
        payload = {
            "assistant_id": assistant_id,
            "stream_mode": ["messages", "updates", "events"],
            "stream_subgraphs": True
        }
        
        if input_data:
            payload["input"] = input_data
        
        if interrupt_before:
            payload["interrupt_before"] = interrupt_before
        
        if interrupt_after:
            payload["interrupt_after"] = interrupt_after
        
        response = requests.post(
            f"{self.base_url}/threads/{thread_id}/runs/stream",
            headers=self.headers,
            json=payload,
            stream=True
        )
        response.raise_for_status()
        
        client = sseclient.SSEClient(response)
        return client
    
    def update_thread_state(self, thread_id: str, values: Dict[str, Any]) -> None:
        """
        Mettre à jour l'état du thread (utilisé après une interruption)
        
        Args:
            thread_id: ID du thread
            values: Valeurs à mettre à jour dans l'état
        """
        payload = {
            "values": values
        }
        
        response = requests.patch(
            f"{self.base_url}/threads/{thread_id}/state",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()

def process_sse_event(event: sseclient.Event) -> Optional[Dict[str, Any]]:
    """Traiter un événement SSE et extraire les données pertinentes"""
    if event.event == "messages/complete":
        messages = json.loads(event.data)
        return {
            "type": "message",
            "messages": messages
        }
    elif event.event == "messages/metadata":
        metadata = json.loads(event.data)
        return {
            "type": "metadata",
            "data": metadata
        }
    elif event.event == "interrupt":
        interrupt_data = json.loads(event.data)
        return {
            "type": "interrupt",
            "data": interrupt_data
        }
    elif event.event == "error":
        error_data = json.loads(event.data)
        return {
            "type": "error",
            "data": error_data
        }
    elif event.event == "end":
        return {
            "type": "end"
        }
    return None

# Interface Streamlit
def main():
    st.title("🤖 Assistant Marketing Campaign LangGraph")
    
    # Initialisation du client
    if "client" not in st.session_state:
        st.session_state.client = LangGraphClient(LANGGRAPH_API_URL, API_KEY)
    
    # Gestion du thread
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = st.session_state.client.create_thread()
        st.session_state.messages = []
        st.session_state.is_interrupted = False
        st.session_state.interrupt_data = None
        st.session_state.run_completed = False
    
    # Afficher l'historique des messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Zone de saisie principale
    if not st.session_state.is_interrupted:
        user_input = st.chat_input("Décrivez votre campagne marketing...")
        
        if user_input:
            # Ajouter le message utilisateur
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            
            with st.chat_message("user"):
                st.write(user_input)
            
            # Lancer le stream avec les interruptions configurées
            with st.spinner("Traitement en cours..."):
                try:
                    # Premier appel avec interruptions configurées
                    stream = st.session_state.client.stream_run(
                        thread_id=st.session_state.thread_id,
                        assistant_id=ASSISTANT_ID,
                        input_data={"messages": [{"role": "user", "content": user_input}]},
                        interrupt_before=["human_feedback", "select_customer_segment"]
                    )
                    
                    # Traiter le stream
                    assistant_response = ""
                    
                    for event in stream.events():
                        processed = process_sse_event(event)
                        
                        if processed:
                            if processed["type"] == "message":
                                # Extraire et afficher les messages
                                for msg in processed["messages"]:
                                    if msg.get("type") == "ai":
                                        assistant_response = msg.get("content", "")

                                        with st.chat_message("assistant"):
                                            st.write(assistant_response)
                                        
                                        st.session_state.messages.append({
                                            "role": "assistant",
                                            "content": assistant_response
                                        })
                            
                            elif processed["type"] == "interrupt":
                                # Gérer l'interruption
                                st.session_state.is_interrupted = True
                                st.session_state.interrupt_data = processed["data"]
                                st.rerun()
                            
                            elif processed["type"] == "end":
                                st.session_state.run_completed = True
                                break
                            
                            elif processed["type"] == "error":
                                st.error(f"Erreur: {processed['data']}")
                                break
                
                except Exception as e:
                    st.error(f"Erreur lors du traitement: {str(e)}")
    
    # Gestion des interruptions
    else:
        st.info("🛑 L'assistant a besoin d'informations supplémentaires")
        
        # Déterminer le type d'interruption
        if st.session_state.interrupt_data:
            interrupt_value = st.session_state.interrupt_data.get("value", "")
            
            # Interruption pour feedback utilisateur
            if "informations manquantes" in interrupt_value.lower():
                user_feedback = st.text_area(
                    "Veuillez fournir les informations manquantes:",
                    key="feedback_input"
                )
                
                if st.button("Soumettre"):
                    if user_feedback:
                        # Mettre à jour l'état avec le feedback
                        st.session_state.client.update_thread_state(
                            st.session_state.thread_id,
                            {"user_feedback": user_feedback}
                        )
                        
                        # Continuer le run
                        st.session_state.is_interrupted = False
                        st.session_state.interrupt_data = None
                        
                        # Relancer le stream sans input (continue from interrupt)
                        with st.spinner("Reprise du traitement..."):
                            stream = st.session_state.client.stream_run(
                                thread_id=st.session_state.thread_id,
                                assistant_id=ASSISTANT_ID
                            )
                            
                            # Traiter la suite du stream
                            for event in stream.events():
                                processed = process_sse_event(event)
                                if processed and processed["type"] == "message":
                                    for msg in processed["messages"]:
                                        if msg.get("type") == "ai":
                                            content = msg.get("content", "")
                                            with st.chat_message("assistant"):
                                                st.write(content)
                                            st.session_state.messages.append({
                                                "role": "assistant",
                                                "content": content
                                            })
                        
                        st.rerun()
            
            # Interruption pour sélection de segment
            elif "segment" in interrupt_value.lower():
                segment_choice = st.selectbox(
                    "Choisissez un segment client:",
                    options=[0, 1, 2, 3],
                    format_func=lambda x: f"Segment {x}"
                )
                
                if st.button("Confirmer la sélection"):
                    # Mettre à jour l'état avec le choix
                    st.session_state.client.update_thread_state(
                        st.session_state.thread_id,
                        {"id_choice_segment": segment_choice}
                    )
                    
                    # Continuer le run
                    st.session_state.is_interrupted = False
                    st.session_state.interrupt_data = None
                    
                    with st.spinner("Génération du persona visuel..."):
                        stream = st.session_state.client.stream_run(
                            thread_id=st.session_state.thread_id,
                            assistant_id=ASSISTANT_ID
                        )
                        
                        for event in stream.events():
                            processed = process_sse_event(event)
                            if processed and processed["type"] == "message":
                                for msg in processed["messages"]:
                                    if msg.get("type") == "ai":
                                        content = msg.get("content", "")
                                        with st.chat_message("assistant"):
                                            st.write(content)
                                            
                                            # Vérifier si l'image est générée
                                            if "image_url" in content or "https://" in content:
                                                # Extraire et afficher l'URL de l'image
                                                import re
                                                urls = re.findall(r'https://[^\s]+', content)
                                                for url in urls:
                                                    if any(ext in url for ext in ['.png', '.jpg', '.jpeg']):
                                                        st.image(url)
                                        
                                        st.session_state.messages.append({
                                            "role": "assistant",
                                            "content": content
                                        })
                    
                    st.rerun()
    
    # Bouton de réinitialisation
    if st.sidebar.button("Nouvelle conversation"):
        for key in ["thread_id", "messages", "is_interrupted", "interrupt_data", "run_completed"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    # Afficher les infos de debug
    with st.sidebar:
        st.subheader("Debug Info")
        st.write(f"Thread ID: {st.session_state.get('thread_id', 'N/A')}")
        st.write(f"Interrupted: {st.session_state.get('is_interrupted', False)}")
        st.write(f"Completed: {st.session_state.get('run_completed', False)}")

if __name__ == "__main__":
    main()