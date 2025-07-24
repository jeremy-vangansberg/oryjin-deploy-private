from client import SimpleLangGraphClient, ASSISTANT_ID
import time

# Initialisation du client
client = SimpleLangGraphClient(
    base_url="http://0.0.0.0:8000",
    api_key="lsv2_sk_c8c6d1234567890abcdef"
)

def test_workflow():
    print("Création d'un nouveau thread...")
    thread_id = client.create_thread()
    print(f"Thread créé : {thread_id}")

    print("\nDémarrage d'un run (stream)...")
    input_data = {"user_message": "Bonjour, assistant !"}
    stream = client.start_run_stream(thread_id, ASSISTANT_ID, input_data)
    print("Réponse de l'assistant (streaming):")
    for event in stream.events():
        if event.data:
            print(event.data)
        # Pour un test simple, on arrête après quelques messages
        time.sleep(0.1)
    
    print("\nRécupération de l'état du thread...")
    state = client.get_thread_state(thread_id)
    print(state)

if __name__ == "__main__":
    test_workflow() 