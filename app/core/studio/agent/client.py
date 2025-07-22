import requests
import json
import re
import asyncio
import chainlit as cl

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
                            content = message['content'].replace('\\n', '\n').replace('\\xe2\\x80\\xa2', '•').replace('\\xc3\\xa9', 'é').replace('\\xc3\\xa0', 'à').replace('\\xf0\\x9f\\x93\\x8a', '📊').replace('\\xf0\\x9f\\x8e\\xaf', '🎯').replace('\\xf0\\x9f\\x8f\\xa1', '🏡').replace('\\xf0\\x9f\\x92\\xbc', '💼').replace('\\xf0\\x9f\\x8f\\xa2', '🏢').replace('\\xe2\\x82\\xac', '€').replace('\\xc3\\x82', 'Â')
                            
                            # Nettoyer le contenu des caractères d'échappement restants
                            content = re.sub(r'\\x[0-9a-f]{2}', '', content)
                            content = re.sub(r'\\[\\"]', lambda m: m.group(0)[1:], content)
                            
                            messages.append(content)
            except json.JSONDecodeError:
                continue
    return messages

@cl.on_message
async def on_message(msg: cl.Message):
    # Message de traitement en cours
    current_step_message = cl.Message(content="🔄 Traitement en cours...")
    await current_step_message.send()
    
    try:
        # Préparer la requête
        payload = {
            "assistant_id": ASSISTANT_ID,
            "input": {
                "messages": [
                    {
                        "type": "human", 
                        "content": msg.content
                    }
                ]
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": API_KEY
        }
        
        # Faire la requête HTTP
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            # Parser les événements SSE
            events = parse_sse_events(response.text)
            
            # Extraire les messages IA
            ai_messages = extract_ai_messages(events)
            
            # Envoyer chaque message séparément
            for i, message in enumerate(ai_messages):
                if message.strip():  # Ne pas envoyer les messages vides
                    step_message = cl.Message(
                        content=f"**🎯 Étape {i+1}:**\n\n{message}"
                    )
                    await step_message.send()
                    # Petite pause entre les messages pour une meilleure UX
                    await asyncio.sleep(0.5)
                    
            if not ai_messages:
                await cl.Message(content="🤔 Aucun contenu trouvé dans la réponse de l'API.").send()
                
        else:
            await cl.Message(content=f"❌ Erreur API: {response.status_code}\n{response.text[:200]}...").send()
            
    except requests.exceptions.Timeout:
        await cl.Message(content="⏰ Timeout: La requête a pris trop de temps à traiter.").send()
    except requests.exceptions.RequestException as e:
        await cl.Message(content=f"❌ Erreur de requête: {str(e)}").send()
    except Exception as e:
        await cl.Message(content=f"❌ Erreur inattendue: {str(e)}").send()
    
    # Supprimer le message de traitement
    await current_step_message.remove()