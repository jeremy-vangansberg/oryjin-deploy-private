from graph2 import graph, user_segment_input
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
import graph2

import chainlit as cl

@cl.on_message
async def on_message(msg: cl.Message):
    config = {"configurable": {"thread_id": cl.context.session.id}}
    cb = cl.LangchainCallbackHandler()
    
    # Dictionnaire pour regrouper les messages par étape
    step_messages = {}
    
    # Créer un message pour chaque étape
    current_step_message = cl.Message(content="🔄 Traitement en cours...")
    await current_step_message.send()
    
    try:
        # Première exécution jusqu'à l'interruption
        for msg_stream, metadata in graph.stream(
            {"messages": [HumanMessage(content=msg.content)]}, 
            stream_mode="messages", 
            config=RunnableConfig(callbacks=[cb], **config)
        ):
            # Regrouper les messages par étape
            if (
                msg_stream.content
                and isinstance(msg_stream, AIMessage)
                and metadata.get("langgraph_node")
            ):
                node_name = metadata["langgraph_node"]
                
                # Regrouper tous les messages d'une étape
                if node_name not in step_messages:
                    step_messages[node_name] = []
                step_messages[node_name].append(msg_stream.content)
        
        # Envoyer un message par étape
        for node_name, messages in step_messages.items():
            combined_content = "\n".join(messages)
            step_message = cl.Message(
                content=f"**🎯 Étape: {node_name}**\n\n{combined_content}"
            )
            await step_message.send()
        
        # Vérifier s'il y a une interruption
        state = graph.get_state(config)
        if state.next:  # Il y a une interruption
            # Afficher les segments disponibles pour aider l'utilisateur
            current_state = state.values
            if "personas" in current_state and current_state["personas"]:
                personas = current_state["personas"]
                segments_info = "\n".join([
                    f"**Segment {i}**: {persona.description_general[:100]}..." 
                    if persona.description_general 
                    else f"**Segment {i}**: Cluster {persona.cluster}"
                    for i, persona in enumerate(personas.personas)
                ])
                
                await cl.Message(content=f"**📋 Segments disponibles:**\n\n{segments_info}").send()
            
            # Demander à l'utilisateur de choisir un segment
            user_input = await cl.AskUserMessage(
                content="Veuillez saisir le numéro du segment que vous souhaitez sélectionner :",
                timeout=60
            ).send()
            
            if user_input:
                # Définir l'input utilisateur dans la variable globale
                graph2.user_segment_input = user_input.content
                
                # Dictionnaire pour les messages de continuation
                continuation_messages = {}
                
                # Reprendre l'exécution 
                for msg_stream, metadata in graph.stream(
                    None,  # Pas de nouveau message
                    stream_mode="messages",
                    config=RunnableConfig(callbacks=[cb], **config)
                ):
                    # Regrouper les messages par étape
                    if (
                        msg_stream.content
                        and isinstance(msg_stream, AIMessage)
                        and metadata.get("langgraph_node")
                    ):
                        node_name = metadata["langgraph_node"]
                        
                        # Regrouper tous les messages d'une étape
                        if node_name not in continuation_messages:
                            continuation_messages[node_name] = []
                        continuation_messages[node_name].append(msg_stream.content)
                
                # Envoyer un message par étape pour la continuation
                for node_name, messages in continuation_messages.items():
                    combined_content = "\n".join(messages)
                    step_message = cl.Message(
                        content=f"**🎯 Étape: {node_name}**\n\n{combined_content}"
                    )
                    await step_message.send()
        
    except Exception as e:
        await cl.Message(content=f"❌ Erreur: {str(e)}").send()
    
    # Supprimer le message de traitement
    await current_step_message.remove()