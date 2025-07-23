import streamlit as st
import requests
import json
import re
import time
from typing import Dict, Any, Optional

# Configuration
LANGGRAPH_API_URL = "https://ht-nautical-decoration-70-7d3b580d2cc25c4fb59221f2145e155e.us.langgraph.app"
API_KEY = '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'
ASSISTANT_ID = "a46dc375-f340-533e-9fe2-61f90b126e72"

class SimpleLangGraphClient:
    def __init__(self):
        self.headers = {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        }
    
    def create_thread(self) -> str:
        """Créer un nouveau thread"""
        response = requests.post(
            f"{LANGGRAPH_API_URL}/threads",
            headers=self.headers,
            json={}
        )
        response.raise_for_status()
        return response.json()["thread_id"]
    
    def get_thread_state(self, thread_id: str) -> Dict[str, Any]:
        """Obtenir l'état actuel du thread"""
        response = requests.get(
            f"{LANGGRAPH_API_URL}/threads/{thread_id}/state",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def start_run(self, thread_id: str, input_data: Dict[str, Any]) -> str:
        """Démarrer un run sans streaming d'abord"""
        payload = {
            "assistant_id": ASSISTANT_ID,
            "input": input_data,
            "interrupt_before": ["human_feedback", "select_customer_segment"]
        }
        
        response = requests.post(
            f"{LANGGRAPH_API_URL}/threads/{thread_id}/runs",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()["run_id"]
    
    def continue_run(self, thread_id: str) -> str:
        """Continuer un run après interruption"""
        payload = {
            "assistant_id": ASSISTANT_ID
        }
        
        response = requests.post(
            f"{LANGGRAPH_API_URL}/threads/{thread_id}/runs",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()["run_id"]
    
    def wait_for_run_completion(self, thread_id: str, run_id: str, max_wait: int = 60):
        """Attendre la fin du run ou une interruption"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            response = requests.get(
                f"{LANGGRAPH_API_URL}/threads/{thread_id}/runs/{run_id}",
                headers=self.headers
            )
            response.raise_for_status()
            run_status = response.json()
            
            status = run_status.get("status")
            
            if status == "success":
                return {"status": "completed", "data": run_status}
            elif status == "interrupted":
                return {"status": "interrupted", "data": run_status}
            elif status == "error":
                return {"status": "error", "data": run_status}
            
            time.sleep(1)
        
        return {"status": "timeout"}
    
    def update_thread_values(self, thread_id: str, values: Dict[str, Any]):
        """Mettre à jour les valeurs du thread"""
        response = requests.patch(
            f"{LANGGRAPH_API_URL}/threads/{thread_id}/state",
            headers=self.headers,
            json={"values": values}
        )
        response.raise_for_status()
    
    def get_thread_messages(self, thread_id: str):
        """Récupérer tous les messages du thread"""
        state = self.get_thread_state(thread_id)
        return state.get("values", {}).get("messages", [])

def extract_ai_messages(messages):
    """Extraire uniquement les messages de l'IA"""
    ai_messages = []
    for msg in messages:
        if hasattr(msg, 'type') and msg.type == 'ai':
            ai_messages.append(msg.content)
        elif isinstance(msg, dict) and msg.get('type') == 'ai':
            ai_messages.append(msg.get('content', ''))
    return ai_messages

def main():
    st.title("🤖 Assistant Marketing Campaign LangGraph")
    st.caption("🔄 **Version simplifiée avec gestion d'interruptions**")
    
    # Initialisation
    if "client" not in st.session_state:
        st.session_state.client = SimpleLangGraphClient()
    
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = st.session_state.client.create_thread()
        st.session_state.conversation_messages = []
        st.session_state.waiting_for_input = False
        st.session_state.interrupt_type = None
    
    # Affichage des messages de conversation
    for msg in st.session_state.conversation_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Interface utilisateur principale
    if not st.session_state.waiting_for_input:
        # Zone de saisie normale
        user_input = st.chat_input("Décrivez votre campagne marketing...")
        
        if user_input:
            # Ajouter le message utilisateur
            st.session_state.conversation_messages.append({
                "role": "user", 
                "content": user_input
            })
            
            with st.chat_message("user"):
                st.write(user_input)
            
            # Démarrer le processus
            with st.spinner("🔄 Traitement en cours..."):
                try:
                    # Démarrer le run
                    run_id = st.session_state.client.start_run(
                        st.session_state.thread_id,
                        {"messages": [{"role": "user", "content": user_input}]}
                    )
                    
                    # Attendre la completion ou interruption
                    result = st.session_state.client.wait_for_run_completion(
                        st.session_state.thread_id, run_id
                    )
                    
                    if result["status"] == "completed":
                        # Récupérer et afficher les nouveaux messages
                        all_messages = st.session_state.client.get_thread_messages(st.session_state.thread_id)
                        ai_messages = extract_ai_messages(all_messages)
                        
                        if ai_messages:
                            latest_ai_message = ai_messages[-1]
                            with st.chat_message("assistant"):
                                st.write(latest_ai_message)
                            
                            st.session_state.conversation_messages.append({
                                "role": "assistant",
                                "content": latest_ai_message
                            })
                    
                    elif result["status"] == "interrupted":
                        # Gérer l'interruption
                        st.session_state.waiting_for_input = True
                        
                        # Récupérer les messages pour voir où on en est
                        all_messages = st.session_state.client.get_thread_messages(st.session_state.thread_id)
                        ai_messages = extract_ai_messages(all_messages)
                        
                        if ai_messages:
                            latest_ai_message = ai_messages[-1]
                            with st.chat_message("assistant"):
                                st.write(latest_ai_message)
                            
                            st.session_state.conversation_messages.append({
                                "role": "assistant",
                                "content": latest_ai_message
                            })
                            
                            # Déterminer le type d'interruption
                            if "informations manquantes" in latest_ai_message.lower():
                                st.session_state.interrupt_type = "feedback"
                            elif "segment" in latest_ai_message.lower():
                                st.session_state.interrupt_type = "segment_selection"
                        
                        st.rerun()
                    
                    elif result["status"] == "error":
                        st.error(f"❌ Erreur: {result['data']}")
                    
                    else:
                        st.error("⏰ Timeout - Le processus prend trop de temps")
                
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
    
    else:
        # Interface d'interruption
        st.info("🛑 L'assistant a besoin d'informations supplémentaires")
        
        if st.session_state.interrupt_type == "feedback":
            # Interface pour feedback utilisateur
            user_feedback = st.text_area(
                "Complétez les informations manquantes ou tapez 'ok' pour continuer:",
                key="feedback_input"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📝 Soumettre feedback"):
                    if user_feedback:
                        # Mettre à jour l'état avec le feedback
                        st.session_state.client.update_thread_values(
                            st.session_state.thread_id,
                            {"user_feedback": user_feedback}
                        )
                        
                        # Ajouter à la conversation
                        st.session_state.conversation_messages.append({
                            "role": "user",
                            "content": user_feedback
                        })
                        
                        # Continuer le processus
                        st.session_state.waiting_for_input = False
                        st.session_state.interrupt_type = None
                        
                        with st.spinner("🔄 Reprise du traitement..."):
                            try:
                                # Continuer le run
                                run_id = st.session_state.client.continue_run(st.session_state.thread_id)
                                
                                # Attendre la completion
                                result = st.session_state.client.wait_for_run_completion(
                                    st.session_state.thread_id, run_id
                                )
                                
                                # Traiter le résultat
                                if result["status"] == "completed":
                                    all_messages = st.session_state.client.get_thread_messages(st.session_state.thread_id)
                                    ai_messages = extract_ai_messages(all_messages)
                                    
                                    if ai_messages:
                                        # Prendre les nouveaux messages
                                        new_messages = ai_messages[len([m for m in st.session_state.conversation_messages if m["role"] == "assistant"]):]
                                        for msg in new_messages:
                                            st.session_state.conversation_messages.append({
                                                "role": "assistant",
                                                "content": msg
                                            })
                                
                                elif result["status"] == "interrupted":
                                    # Nouvelle interruption
                                    all_messages = st.session_state.client.get_thread_messages(st.session_state.thread_id)
                                    ai_messages = extract_ai_messages(all_messages)
                                    
                                    if ai_messages:
                                        latest_ai_message = ai_messages[-1]
                                        st.session_state.conversation_messages.append({
                                            "role": "assistant",
                                            "content": latest_ai_message
                                        })
                                        
                                        # Déterminer le nouveau type d'interruption
                                        if "segment" in latest_ai_message.lower():
                                            st.session_state.interrupt_type = "segment_selection"
                                            st.session_state.waiting_for_input = True
                            
                            except Exception as e:
                                st.error(f"❌ Erreur lors de la reprise: {str(e)}")
                        
                        st.rerun()
            
            with col2:
                if st.button("✅ Continuer (OK)"):
                    # Envoyer "ok" pour forcer la continuation
                    st.session_state.client.update_thread_values(
                        st.session_state.thread_id,
                        {"user_feedback": "ok"}
                    )
                    
                    st.session_state.conversation_messages.append({
                        "role": "user",
                        "content": "ok"
                    })
                    
                    st.session_state.waiting_for_input = False
                    st.session_state.interrupt_type = None
                    st.rerun()
        
        elif st.session_state.interrupt_type == "segment_selection":
            # Interface pour sélection de segment
            segment_choice = st.selectbox(
                "Choisissez un segment client:",
                options=[0, 1, 2, 3],
                format_func=lambda x: f"Segment {x}"
            )
            
            if st.button("🎯 Confirmer la sélection"):
                # Mettre à jour avec le choix
                st.session_state.client.update_thread_values(
                    st.session_state.thread_id,
                    {"id_choice_segment": segment_choice}
                )
                
                st.session_state.conversation_messages.append({
                    "role": "user",
                    "content": f"Segment choisi: {segment_choice}"
                })
                
                st.session_state.waiting_for_input = False
                st.session_state.interrupt_type = None
                
                with st.spinner("🎨 Génération du persona visuel..."):
                    try:
                        # Continuer le run
                        run_id = st.session_state.client.continue_run(st.session_state.thread_id)
                        
                        # Attendre la completion
                        result = st.session_state.client.wait_for_run_completion(
                            st.session_state.thread_id, run_id
                        )
                        
                        if result["status"] == "completed":
                            all_messages = st.session_state.client.get_thread_messages(st.session_state.thread_id)
                            ai_messages = extract_ai_messages(all_messages)
                            
                            if ai_messages:
                                latest_ai_message = ai_messages[-1]
                                st.session_state.conversation_messages.append({
                                    "role": "assistant",
                                    "content": latest_ai_message
                                })
                    
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la génération: {str(e)}")
                
                st.rerun()
    
    # Sidebar avec infos de debug
    with st.sidebar:
        st.subheader("🔧 Debug Info")
        st.write(f"**Thread ID:** `{st.session_state.thread_id[:8]}...`")
        st.write(f"**Waiting for input:** {st.session_state.waiting_for_input}")
        st.write(f"**Interrupt type:** {st.session_state.interrupt_type}")
        st.write(f"**Messages count:** {len(st.session_state.conversation_messages)}")
        
        if st.button("🔄 Nouvelle conversation"):
            for key in ["thread_id", "conversation_messages", "waiting_for_input", "interrupt_type"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()