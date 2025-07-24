import asyncio
from langgraph_sdk import get_client
from langchain_core.messages import HumanMessage
from langchain_core.messages import convert_to_messages


def parse_messages(chunk):
    if chunk.event == "messages/complete":
        return chunk.data[-1].get('content')
    else:
        return chunk

class StateTracker:
    def __init__(self):
        self.continue_the_loop = True
        self.as_node = None

    def update_continue(self, chunk):
        if chunk.event == "messages/metadata":
            metadata = next(iter(chunk.data.values())).get('metadata', {})
            triggers = metadata.get('langgraph_triggers', [])
            if 'branch:to:generate visual persona' in triggers:
                # Dès que le trigger apparaît une fois, c'est définitif
                self.continue_the_loop = False

    def update_as_node(self, chunk):
        if chunk.event == "messages/metadata":
            metadata = next(iter(chunk.data.values())).get('metadata', {})
            node = metadata.get('langgraph_node', None)
            # Ici, tu peux spécifier la priorité des nodes
            priority_nodes = ["await_user_clarification", "await_segment_selection"]
            if node in priority_nodes:
                # Prendre celui avec la priorité la plus haute (premier dans la liste)
                if (self.as_node is None or
                    priority_nodes.index(node) < priority_nodes.index(self.as_node)):
                    self.as_node = node

async def main():
    client = get_client(url="http://127.0.0.1:2024")

    thread = await client.threads.create()
    assistant_id = "dsp_assistant"
    scenario_inputs = [
        "Je veux créer une campagne marketing pour des produits de beauté bio",
        "Je suis le directeur marketing d'une enseigne de distribution, équipement de la maison, grand public, je vends sur le web et en magasin. On est haut de gamme. Ma clientèle est CSP+. Je veux faire une campagne de recrutement de nouveaux clients sur un produit moyen gamme de façon à recruter autant sur les CSP que les CSP+. Je souhaite définir les paramètres pour ma campagne display sur Pmax de google.",
        "2"
    ]

    state_tracker = StateTracker()

    # Premier run initial
    stream = client.runs.stream(
        thread_id=thread["thread_id"],
        assistant_id=assistant_id,
        input={"messages": [HumanMessage(content=scenario_inputs[0])]},
        stream_mode="messages",
        interrupt_before=["await_user_clarification"]
    )

    async for chunk in stream:
        print(parse_messages(chunk))
        state_tracker.update_as_node(chunk)
        state_tracker.update_continue(chunk)

    # Boucle principale
    while state_tracker.continue_the_loop:

        update_run = await client.threads.update_state(
            thread_id=thread["thread_id"],
            values={"messages": [HumanMessage(content=input("saisir : "))]},
            as_node=state_tracker.as_node
        )

        resume = client.runs.stream(
            thread_id=thread["thread_id"],
            assistant_id=assistant_id,
            input=None,
            stream_mode="messages",
            interrupt_before=["await_user_clarification", "await_segment_selection"]
        )

        async for chunk in resume:
            print(parse_messages(chunk))
            state_tracker.update_as_node(chunk)
            state_tracker.update_continue(chunk)

    print("✅ Fin de la boucle atteinte !")

if __name__ == "__main__":
    # Lancer l'exécution asynchrone
    asyncio.run(main())
