"""
CLIENT STREAMLIT MINIMAL POUR LANGGRAPH API
===========================================

- À chaque message utilisateur, POST /threads/{thread_id}/runs/stream avec interrupt_before
- Affiche tous les messages IA reçus dans le stream
- Si interruption, affiche la demande et attend la saisie utilisateur
- Historique des messages conservé
"""

import streamlit as st
import requests
import json
import sseclient

LANGGRAPH_API_URL = "http://0.0.0.0:8000"
API_KEY = "lsv2_sk_c8c6d1234567890abcdef"
ASSISTANT_ID = "dsp_assistant"

HEADERS = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

class MinimalLangGraphClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }
    def create_thread(self):
        response = requests.post(f"{self.base_url}/threads", headers=self.headers, json={})
        response.raise_for_status()
        return response.json()["thread_id"]
    def start_run_stream(self, thread_id, assistant_id, input_data):
        payload = {
            "assistant_id": assistant_id,
            "input": input_data,
            "stream_mode": ["values", "messages", "events"],
            "interrupt_before": ["await_user_clarification", "await_segment_selection"]
        }
        response = requests.post(
            f"{self.base_url}/threads/{thread_id}/runs/stream",
            headers=self.headers,
            json=payload,
            stream=True
        )
        response.raise_for_status()
        return sseclient.SSEClient(response)

def process_sse_stream(stream):
    messages = []
    interrupted = False
    interrupt_message = None
    for event in stream.events():
        if not event.data or event.data.strip() == "[DONE]":
            continue
        try:
            data = json.loads(event.data)
        except Exception:
            continue
        if event.event == "messages/complete":
            for msg in data:
                if msg.get("type") == "ai":
                    content = msg.get("content", "").strip()
                    if content:
                        messages.append({"role": "assistant", "content": content})
                        # Afficher immédiatement le message IA
                        with st.chat_message("assistant"):
                            st.write(content)
        elif event.event == "values":
            if "messages" in data:
                for msg in data["messages"]:
                    if msg.get("type") == "ai":
                        content = msg.get("content", "").strip()
                        if content:
                            messages.append({"role": "assistant", "content": content})
                            with st.chat_message("assistant"):
                                st.write(content)
        elif event.event == "interrupt":
            interrupted = True
            interrupt_message = data.get("value") or "L'assistant a besoin d'une précision."
            break
    return messages, interrupted, interrupt_message

def display_messages():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

def main():
    st.title("🤖 Assistant Marketing Campaign (Minimal)")
    if "client" not in st.session_state:
        st.session_state.client = MinimalLangGraphClient(LANGGRAPH_API_URL, API_KEY)
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = st.session_state.client.create_thread()
        st.session_state.messages = []
        st.session_state.interrupted = False
        st.session_state.interrupt_message = None
    display_messages()
    if st.session_state.get("interrupted", False):
        st.info(st.session_state.get("interrupt_message", "L'assistant a besoin d'une précision."))
        user_response = st.chat_input("Votre réponse...")
        if user_response:
            st.session_state.messages.append({"role": "user", "content": user_response})
            with st.chat_message("user"):
                st.write(user_response)
            st.session_state.interrupted = False
            st.session_state.interrupt_message = None
            with st.spinner("Traitement en cours..."):
                input_data = {"messages": [{"role": "human", "content": user_response}]}
                stream = st.session_state.client.start_run_stream(
                    thread_id=st.session_state.thread_id,
                    assistant_id=ASSISTANT_ID,
                    input_data=input_data
                )
                ai_messages, interrupted, interrupt_message = process_sse_stream(stream)
                st.session_state.messages.extend(ai_messages)
                st.session_state.interrupted = interrupted
                st.session_state.interrupt_message = interrupt_message
            st.rerun()
    else:
        if not st.session_state.messages:
            st.info("👋 Décrivez votre campagne marketing pour commencer.")
        user_input = st.chat_input("Décrivez votre campagne marketing...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)
            with st.spinner("Traitement en cours..."):
                input_data = {"messages": [{"role": "human", "content": user_input}]}
                stream = st.session_state.client.start_run_stream(
                    thread_id=st.session_state.thread_id,
                    assistant_id=ASSISTANT_ID,
                    input_data=input_data
                )
                ai_messages, interrupted, interrupt_message = process_sse_stream(stream)
                st.session_state.messages.extend(ai_messages)
                st.session_state.interrupted = interrupted
                st.session_state.interrupt_message = interrupt_message
            st.rerun()
    with st.sidebar:
        if st.button("Nouvelle conversation"):
            for key in ["thread_id", "messages", "interrupted", "interrupt_message"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
