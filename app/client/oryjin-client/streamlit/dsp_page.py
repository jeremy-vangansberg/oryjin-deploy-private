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
    elif chunk.event == "messages/partial":
        # Traiter aussi les messages partiels pour le streaming
        if chunk.data and len(chunk.data) > 0:
            return chunk.data[-1].get('content', '')
    return None

class StateTracker:
    """Suit l'état de la conversation et détermine quand continuer"""
    def __init__(self):
        self.continue_the_loop = True
        self.as_node = None

    def update_continue(self, chunk):
        """Met à jour si on doit continuer la boucle"""
        # Pour l'instant, ne pas terminer automatiquement
        # Laissons le stream se terminer naturellement
        pass
    
    def set_conversation_ended(self):
        """Marque la conversation comme terminée (appelé après la fin du stream)"""
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
        interrupt_before=["await_user_clarification", "await_segment_selection"]
    )
    
    messages = []
    full_response = ""
    state_tracker = StateTracker()
    
    async for chunk in stream:
        # Debug : afficher les informations de chaque chunk
        print(f"DEBUG - Chunk event: {chunk.event}")
        if hasattr(chunk, 'data') and chunk.data:
            print(f"DEBUG - Chunk data keys: {list(chunk.data.keys()) if isinstance(chunk.data, dict) else 'not dict'}")
        
        content = parse_messages(chunk)
        if content and isinstance(content, str) and content.strip():
            # Pour les messages partiels, on accumule le contenu
            if chunk.event == "messages/partial":
                # Remplacer le dernier message s'il existe, sinon ajouter
                if messages and len(messages) > 0:
                    messages[-1] = content
                else:
                    messages.append(content)
                # Reconstruire la réponse complète
                full_response = "\n\n".join(messages) + "\n\n"
            else:
                # Message complet
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
        # Debug : afficher les informations de chaque chunk
        print(f"DEBUG - Resume chunk event: {chunk.event}")
        if hasattr(chunk, 'data') and chunk.data:
            print(f"DEBUG - Resume chunk data keys: {list(chunk.data.keys()) if isinstance(chunk.data, dict) else 'not dict'}")
        
        content = parse_messages(chunk)
        if content and isinstance(content, str) and content.strip():
            # Pour les messages partiels, on accumule le contenu
            if chunk.event == "messages/partial":
                # Remplacer le dernier message s'il existe, sinon ajouter
                if messages and len(messages) > 0:
                    messages[-1] = content
                else:
                    messages.append(content)
                # Reconstruire la réponse complète
                full_response = "\n\n".join(messages) + "\n\n"
            else:
                # Message complet
                messages.append(content)
                full_response += content + "\n\n"
            
            # Mise à jour en temps réel du placeholder
            placeholder.markdown(full_response)
        
        state_tracker.update_as_node(chunk)
        state_tracker.update_continue(chunk)
    
    # Après la fin du stream, vérifier si on doit terminer
    # Si aucun node d'interruption n'est actif, c'est que le graphe est terminé
    if state_tracker.as_node is None or state_tracker.as_node not in ["await_user_clarification", "await_segment_selection"]:
        print("DEBUG - Stream terminé sans interruption, fin de conversation")
        state_tracker.set_conversation_ended()
    
    return messages, state_tracker, full_response

def run_async_in_streamlit(coro, loop):
    """Exécute une coroutine dans l'event loop de Streamlit"""
    return loop.run_until_complete(coro)

def check_authentication():
    """Vérifie l'authentification de l'utilisateur"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Accès Sécurisé")
        st.markdown("""
        <div style='text-align: center; margin-bottom: 30px;'>
            <p style='font-size: 1.2em; color: #6c757d;'>
                Veuillez entrer le code d'accès pour utiliser l'assistant marketing
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Formulaire d'authentification
        with st.form("auth_form"):
            access_code = st.text_input(
                "Code d'accès", 
                type="password",
                placeholder="Entrez votre code d'accès"
            )
            submit_button = st.form_submit_button("🚀 Accéder à l'assistant")
            
            if submit_button:
                # TODO: Remplacer par le code souhaité par l'utilisateur
                correct_code = "ORYJIN2025"  # Code temporaire
                
                if access_code == correct_code:
                    st.session_state.authenticated = True
                    st.success("✅ Authentification réussie ! Redirection en cours...")
                    st.rerun()
                else:
                    st.error("❌ Code d'accès incorrect. Veuillez réessayer.")
        
        # Informations de contact (optionnel)
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #888; font-size: 0.9em;'>
            <p>Besoin d'aide ? Contactez l'administrateur pour obtenir votre code d'accès.</p>
        </div>
        """, unsafe_allow_html=True)
        
        return False
    
    return True

def main():
    # Configuration de la page
    st.set_page_config(
        page_title="Assistant Marketing Oryjin",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Vérifier l'authentification avant d'afficher le contenu
    if not check_authentication():
        return
    
    # Interface principale (accessible uniquement après authentification)
    
    st.title("🤖 Assistant Marketing Oryjin")
    st.markdown("""
    <div style='text-align: center; margin-bottom: 30px;'>
        <p style='font-size: 1.2em; color: #6c757d; font-style: italic;'>
            Votre assistant IA pour créer des campagnes marketing personnalisées
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Ajouter du CSS pour le scroll automatique et améliorer l'UI
    st.markdown("""
    <style>
    .stApp > div:first-child {
        overflow-x: hidden;
    }
    .main .block-container {
        padding-bottom: 2rem;
    }
    /* Scroll automatique vers le bas */
    .element-container:last-child {
        animation: scrollToBottom 0.3s ease-out;
    }
    @keyframes scrollToBottom {
        from { opacity: 0.7; }
        to { opacity: 1; }
    }
    /* Style pour les messages importants */
    .important-message {
        border: 2px solid #ff6b6b;
        border-radius: 10px;
        padding: 15px;
        background-color: #fff5f5;
        margin: 10px 0;
    }
    

    
    /* Amélioration du design général */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main > div {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        margin: 20px;
        padding: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    
    /* Style amélioré pour les messages de chat */
    .stChatMessage {
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Style pour le titre */
    h1 {
        text-align: center;
        color: #2c3e50;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }
    </style>
    <script>
    // Fonction pour scroll automatique vers le bas
    function scrollToBottom() {
        window.scrollTo(0, document.body.scrollHeight);
    }
    // Exécuter après un court délai pour laisser le temps au contenu de se charger
    setTimeout(scrollToBottom, 100);
    </script>
    """, unsafe_allow_html=True)
    
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
        st.markdown("Décrivez votre projet marketing dans le chat ci-dessous...")
        
        # Chat input pour le message initial
        if initial_message := st.chat_input("Ex: Je veux créer une campagne marketing pour..."):
            # Afficher le message utilisateur
            st.session_state.messages.append({"role": "user", "content": initial_message})
            with st.chat_message("user"):
                st.markdown(initial_message)
            
            # Créer un placeholder pour la réponse streaming
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                
                with st.spinner("🔄 L'assistant analyse votre demande..."):
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
                        
                        # Vérifier si la conversation est terminée dès l'initialisation
                        if not st.session_state.state_tracker.continue_the_loop:
                            st.session_state.conversation_ended = True
                            st.success("✅ Conversation terminée !")
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erreur lors de l'initialisation: {e}")
                        st.error("Assurez-vous que votre API LangGraph est en cours d'exécution sur http://127.0.0.1:2024")
    
    else:
        # Conversation en cours - Afficher l'historique des messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Interface de saisie - Continue tant que continue_the_loop est True
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
                    
                    with st.spinner("🔄 L'assistant prépare sa réponse..."):
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
                            
                            # Relancer pour continuer le flux
                            st.rerun()
                                
                        except Exception as e:
                            st.error(f"Erreur lors de l'envoi du message: {e}")
        
        elif st.session_state.conversation_ended:
            st.success("🎉 La conversation s'est terminée avec succès !")
            
            # Chercher et mettre en évidence l'URL de l'image dans le dernier message
            if st.session_state.messages:
                last_message = st.session_state.messages[-1]
                if "Image générée :" in last_message.get("content", ""):
                    # Extraire l'URL de l'image
                    import re
                    url_match = re.search(r'https://[^\s]+', last_message["content"])
                    if url_match:
                        image_url = url_match.group()
                        st.markdown(f"""
                        <div class="important-message">
                            <h3>🎨 Votre persona visuel est prêt !</h3>
                            <div style="text-align: center; margin: 20px 0;">
                                <a href="{image_url}" target="_blank" 
                                   style="display: inline-block; padding: 12px 24px; 
                                          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                          color: white; text-decoration: none; border-radius: 25px; 
                                          font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                                          transition: transform 0.2s ease;">
                                    🖼️ Voir mon persona visuel
                                </a>
                            </div>
                            <p style="font-size: 0.9em; color: #666; text-align: center;">
                                <strong>URL :</strong> <code style="background: #f8f9fa; padding: 2px 6px; border-radius: 4px;">{image_url}</code>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Scroll automatique vers le bas pour s'assurer que l'URL est visible
            st.markdown("""
            <script>
            setTimeout(function() {
                window.scrollTo(0, document.body.scrollHeight);
            }, 500);
            </script>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Nouvelle conversation"):
                # Réinitialiser pour une nouvelle conversation
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    # Sidebar avec informations de debug et déconnexion
    with st.sidebar:
        st.header("👤 Session")
        st.success("✅ Connecté")
        
        if st.button("🚪 Se déconnecter", type="secondary"):
            # Réinitialiser complètement la session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        st.header("🔧 Debug Info")
        if st.session_state.conversation_started:
            st.write(f"**Thread ID:** {st.session_state.thread_id}")
            st.write(f"**Continue Loop:** {st.session_state.state_tracker.continue_the_loop}")
            st.write(f"**Current Node:** {st.session_state.state_tracker.as_node}")
            st.write(f"**Messages Count:** {len(st.session_state.messages)}")
            st.write(f"**Event Loop:** {id(st.session_state['event_loop'])}")
        else:
            st.write("*Conversation non démarrée*")
        
        if st.button("🔄 Réinitialiser conversation"):
            # Réinitialiser seulement la conversation, pas l'authentification
            keys_to_keep = ["authenticated"]
            keys_to_remove = [key for key in st.session_state.keys() if key not in keys_to_keep]
            for key in keys_to_remove:
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
