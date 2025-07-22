import streamlit as st
import requests
import json
import re

# Configuration de l'API
API_URL = "https://ht-nautical-decoration-70-7d3b580d2cc25c4fb59221f2145e155e.us.langgraph.app/runs/stream"
API_KEY = "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"
ASSISTANT_ID = "fe096781-5601-53d2-b2f6-0d3403f7e9ca"

def parse_sse_events(response_text):
    """Parse Server-Sent Events from response text"""
    events = []
    lines = response_text.split('\n')
    
    current_event = {}
    for line in lines:
        line = line.strip()
        if line.startswith('event:'):
            current_event['event'] = line[6:].strip()
        elif line.startswith('data:'):
            current_event['data'] = line[5:].strip()
            if current_event.get('event') and current_event.get('data'):
                events.append(current_event.copy())
                current_event = {}
    
    return events

def extract_ai_messages(events):
    """Extract AI messages from SSE events"""
    messages = []
    for event in events:
        if event.get('event') == 'values' and event.get('data'):
            try:
                data = json.loads(event['data'])
                if 'messages' in data:
                    for message in data['messages']:
                        if message.get('type') == 'ai' and message.get('content'):
                            # Décoder les caractères échappés
                            content = message['content'].replace('\\n', '\n')
                            # Nettoyer les caractères d'échappement
                            content = re.sub(r'\\x[0-9a-f]{2}', '', content)
                            content = re.sub(r'\\[\\"]', lambda m: m.group(0)[1:], content)
                            
                            if content.strip() and content not in messages:  # Éviter les doublons
                                messages.append(content)
            except json.JSONDecodeError:
                continue
    return messages

# Initialiser l'historique dans la session
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💬 Agent LangGraph Demo")

# Affichage des messages précédents
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Interface utilisateur : champ de saisie
if prompt := st.chat_input("Posez une question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Préparer le payload avec l'input utilisateur
    payload = {
        "assistant_id": ASSISTANT_ID,
        "input": {
            "messages": [
                {
                    "type": "human", 
                    "content": prompt  # Utiliser l'input de l'utilisateur
                }
            ]
        }
    }

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": API_KEY
    }

    # Afficher un spinner pendant le traitement
    with st.chat_message("assistant"):
        with st.spinner("🔄 Traitement en cours..."):
            try:
                # Faire la requête HTTP (pas de json.dumps, juste json=payload)
                response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
                response.raise_for_status()
                
                # Parser les événements SSE
                events = parse_sse_events(response.text)
                
                # Extraire les messages IA
                ai_messages = extract_ai_messages(events)
                
                if ai_messages:
                    # Afficher tous les messages en une seule fois
                    full_response = "\n\n---\n\n".join([f"**🎯 Étape {i+1}:**\n\n{msg}" for i, msg in enumerate(ai_messages)])
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    st.error("🤔 Aucun contenu trouvé dans la réponse de l'API.")
                    
            except requests.exceptions.Timeout:
                st.error("⏰ Timeout: La requête a pris trop de temps à traiter.")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Erreur de requête: {str(e)}")
            except Exception as e:
                st.error(f"❌ Erreur inattendue: {str(e)}")
