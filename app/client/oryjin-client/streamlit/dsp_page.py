import asyncio
import streamlit as st
from langgraph_sdk import get_client
from langchain_core.messages import HumanMessage
import time
from dotenv import load_dotenv
import os
load_dotenv()

def parse_messages(chunk):
    """Parse les messages des chunks reçus de l'API"""
    if chunk.event == "messages/complete":
        return chunk.data[-1].get('content')
    else:
        return chunk

class StateTracker:
    """Suit l'état de la conversation et détermine quand continuer"""
    def __init__(self):
        self.continue_the_loop = True
        self.as_node = None

    def update_continue(self, chunk):
        """Met à jour si on doit continuer la boucle"""
        if chunk.event == "messages/metadata":
            metadata = next(iter(chunk.data.values())).get('metadata', {})
            triggers = metadata.get('langgraph_triggers', [])
            if 'branch:to:generate visual persona' in triggers:
                self.continue_the_loop = False

    def update_as_node(self, chunk):
        """Met à jour le node actuel avec priorité"""
        if chunk.event == "messages/metadata":
            metadata = next(iter(chunk.data.values())).get('metadata', {})
            node = metadata.get('langgraph_node', None)
            priority_nodes = ["await_user_clarification", "await_segment_selection"]
            if node in priority_nodes:
                if (self.as_node is None or
                    priority_nodes.index(node) < priority_nodes.index(self.as_node)):
                    self.as_node = node

@st.cache_resource(show_spinner=False)
def get_event_loop():
    """Workaround pour le problème d'asyncio dans Streamlit (GitHub issue #8488)"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop

@st.cache_resource
def get_langgraph_client():
    """Obtient le client LangGraph (mis en cache)"""
    return get_client(url=os.getenv("LANGGRAPH_URL"), api_key=os.getenv("LANGGRAPH_API_KEY"))

async def create_thread_and_send_initial_message_streaming(client, initial_message, loop, placeholder):
    """Crée un nouveau thread et envoie le message initial avec streaming"""
    # Créer un nouveau thread
    thread = await client.threads.create()
    
    # Premier run initial
    stream = client.runs.stream(
        thread_id=thread["thread_id"],
        assistant_id="dsp_assistant",
        input={"messages": [HumanMessage(content=initial_message)]},
        stream_mode="messages",
        interrupt_before=["await_user_clarification"]
    )
    
    messages = []
    full_response = ""
    state_tracker = StateTracker()
    
    async for chunk in stream:
        content = parse_messages(chunk)
        if content and isinstance(content, str):
            messages.append(content)
            full_response += content + "\n\n"
            # Mise à jour en temps réel du placeholder
            placeholder.markdown(full_response)
        
        state_tracker.update_as_node(chunk)
        state_tracker.update_continue(chunk)
    
    return thread["thread_id"], messages, state_tracker, full_response

async def send_message_streaming(client, thread_id, message, state_tracker, loop, placeholder):
    """Envoie un message et traite la réponse avec streaming"""
    # Mettre à jour l'état du thread
    await client.threads.update_state(
        thread_id=thread_id,
        values={"messages": [HumanMessage(content=message)]},
        as_node=state_tracker.as_node
    )
    
    # Reprendre l'exécution
    resume = client.runs.stream(
        thread_id=thread_id,
        assistant_id="dsp_assistant",
        input=None,
        stream_mode="messages",
        interrupt_before=["await_user_clarification", "await_segment_selection"]
    )
    
    messages = []
    full_response = ""
    
    async for chunk in resume:
        content = parse_messages(chunk)
        if content and isinstance(content, str):
            messages.append(content)
            full_response += content + "\n\n"
            # Mise à jour en temps réel du placeholder
            placeholder.markdown(full_response)
        
        state_tracker.update_as_node(chunk)
        state_tracker.update_continue(chunk)
    
    return messages, state_tracker, full_response

def run_async_in_streamlit(coro, loop):
    """Exécute une coroutine dans l'event loop de Streamlit"""
    return loop.run_until_complete(coro)

def main():
    st.title("🤖 Assistant Marketing Oryjin")
    st.markdown("Interface de chat avec l'assistant marketing")
    
    # Initialiser l'event loop (workaround GitHub issue #8488)
    if not st.session_state.get("event_loop"):
        st.session_state["event_loop"] = get_event_loop()
    
    # Initialiser l'état de session
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.client = None
        st.session_state.thread_id = None
        st.session_state.state_tracker = None
        st.session_state.conversation_ended = False
        st.session_state.conversation_started = False

    # Si la conversation n'a pas encore commencé
    if not st.session_state.conversation_started:
        st.markdown("### 💡 Commencez votre conversation")
        
        # Zone de saisie pour le message initial
        initial_message = st.text_area(
            "Décrivez votre projet marketing :",
            placeholder="Ex: Je veux créer une campagne marketing pour...",
            height=100
        )
        
        if st.button("🚀 Démarrer la conversation", disabled=not initial_message.strip()):
            if initial_message.strip():
                # Afficher le message utilisateur
                st.session_state.messages.append({"role": "user", "content": initial_message})
                with st.chat_message("user"):
                    st.markdown(initial_message)
                
                # Créer un placeholder pour la réponse streaming
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    
                    with st.spinner("Traitement en cours..."):
                        try:
                            # Obtenir le client
                            client = get_langgraph_client()
                            st.session_state.client = client
                            
                            # Créer le thread et envoyer le message initial avec streaming
                            thread_id, initial_messages, state_tracker, full_response = run_async_in_streamlit(
                                create_thread_and_send_initial_message_streaming(
                                    client, 
                                    initial_message, 
                                    st.session_state["event_loop"],
                                    response_placeholder
                                ),
                                st.session_state["event_loop"]
                            )
                            
                            st.session_state.thread_id = thread_id
                            st.session_state.state_tracker = state_tracker
                            st.session_state.conversation_started = True
                            
                            # Ajouter la réponse complète à l'historique
                            if full_response.strip():
                                st.session_state.messages.append({"role": "assistant", "content": full_response.strip()})
                            
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Erreur lors de l'initialisation: {e}")
                            st.error("Assurez-vous que votre API LangGraph est en cours d'exécution sur http://127.0.0.1:2024")
    
    else:
        # Conversation en cours
        # Afficher l'historique des messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Interface de saisie
        if not st.session_state.conversation_ended and st.session_state.state_tracker.continue_the_loop:
            if prompt := st.chat_input("Votre message..."):
                # Ajouter le message utilisateur
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Afficher le message utilisateur immédiatement
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Traiter la réponse avec streaming
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    
                    try:
                        # Envoyer le message et récupérer la réponse avec streaming
                        response_messages, updated_tracker, full_response = run_async_in_streamlit(
                            send_message_streaming(
                                st.session_state.client,
                                st.session_state.thread_id,
                                prompt,
                                st.session_state.state_tracker,
                                st.session_state["event_loop"],
                                response_placeholder
                            ),
                            st.session_state["event_loop"]
                        )
                        
                        # Mettre à jour the state tracker
                        st.session_state.state_tracker = updated_tracker
                        
                        # Ajouter la réponse complète à l'historique
                        if full_response.strip():
                            st.session_state.messages.append({"role": "assistant", "content": full_response.strip()})
                        
                        # Vérifier si la conversation doit se terminer
                        if not st.session_state.state_tracker.continue_the_loop:
                            st.session_state.conversation_ended = True
                            st.success("✅ Conversation terminée !")
                            
                    except Exception as e:
                        st.error(f"Erreur lors de l'envoi du message: {e}")
        
        elif st.session_state.conversation_ended:
            st.info("🎉 La conversation s'est terminée avec succès !")
            if st.button("Nouvelle conversation"):
                # Réinitialiser pour une nouvelle conversation
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    # Sidebar avec informations de debug
    with st.sidebar:
        st.header("🔧 Debug Info")
        if st.session_state.conversation_started:
            st.write(f"**Thread ID:** {st.session_state.thread_id}")
            st.write(f"**Continue Loop:** {st.session_state.state_tracker.continue_the_loop}")
            st.write(f"**Current Node:** {st.session_state.state_tracker.as_node}")
            st.write(f"**Messages Count:** {len(st.session_state.messages)}")
            st.write(f"**Event Loop:** {id(st.session_state['event_loop'])}")
        else:
            st.write("*Conversation non démarrée*")
        
        if st.button("🔄 Réinitialiser"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
