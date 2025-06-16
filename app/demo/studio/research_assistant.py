import operator
from pydantic import BaseModel, Field
from typing import Annotated, List, Tuple
from typing_extensions import TypedDict

from langchain_community.document_loaders import WikipediaLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, get_buffer_string
from langchain_openai import ChatOpenAI

from langgraph.constants import Send
from langgraph.graph import END, MessagesState, START, StateGraph

### LLM

llm = ChatOpenAI(model="gpt-4o", temperature=0) 

### Schema 

class Analyst(BaseModel):
    affiliation: str = Field(
        description="Affiliation principale de l'analyste.",
    )
    name: str = Field(
        description="Nom de l'analyste."
    )
    role: str = Field(
        description="Rôle de l'analyste dans le contexte du sujet.",
    )
    description: str = Field(
        description="Description du focus, des préoccupations et des motivations de l'analyste.",
    )
    @property
    def persona(self) -> str:
        return f"Nom: {self.name}\nRôle: {self.role}\nAffiliation: {self.affiliation}\nDescription: {self.description}\n"

class Perspectives(BaseModel):
    analysts: List[Analyst] = Field(
        description="Liste complète des analystes avec leurs rôles et affiliations.",
    )

class GenerateAnalystsState(MessagesState):
    topic: str # Sujet de recherche
    max_analysts: int # Nombre d'analystes
    human_analyst_feedback: str # Retour humain
    analysts: List[Analyst] # Analyste posant des questions

class InterviewState(MessagesState):
    max_num_turns: int # Nombre de tours de conversation
    context: Annotated[list, operator.add] # Documents sources
    analyst: Analyst # Analyste posant des questions
    interview: str # Transcription de l'entretien
    sections: list # Clé finale que nous dupliquons dans l'état externe pour l'API Send()

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Requête de recherche pour la récupération.")

class ResearchGraphState(MessagesState):
    topic: str # Sujet de recherche
    max_analysts: int # Nombre d'analystes
    human_analyst_feedback: str # Retour humain
    analysts: List[Analyst] # Analyste posant des questions
    sections: Annotated[list, operator.add] # Clé API Send()
    introduction: str # Introduction du rapport final
    content: str # Contenu du rapport final
    conclusion: str # Conclusion du rapport final
    final_report: str # Rapport final

class InitialMessageParse(BaseModel):
    topic: str = Field(description="Le sujet de recherche")
    max_analysts: int = Field(description="Nombre d'analystes (par défaut 3 si non spécifié)")

def parse_initial_message(state: GenerateAnalystsState) -> Tuple[str, int]:
    """Parse le message initial pour extraire le topic et le nombre d'analystes"""
    
    # Récupérer le message initial
    initial_message = state["messages"][0]

    # Instructions pour le parsing
    parse_instructions = f"""Extrayez le sujet de recherche et le nombre d'analystes du message suivant.
    Retournez un JSON avec deux champs :
    - topic: le sujet de recherche
    - max_analysts: le nombre d'analystes (par défaut 3 si non spécifié)
    """
    
    # Utiliser le LLM pour parser
    structured_llm = llm.with_structured_output(InitialMessageParse)
    
    # Parser le message
    result = structured_llm.invoke([
        SystemMessage(content=parse_instructions.format(initial_message=parse_instructions)),
        HumanMessage(content=f"Voici le message : {initial_message.content}")
    ])
    
    return {
        "max_analysts": result.max_analysts,
        "topic": result.topic
    }


def create_analysts(state: GenerateAnalystsState):
    
    """ Create analysts """
    
    topic=state['topic']
    max_analysts=state['max_analysts']
    human_analyst_feedback=state.get('human_analyst_feedback', '')
        
    # Enforce structured output
    structured_llm = llm.with_structured_output(Perspectives)

    # System message
    system_message = analyst_instructions.format(topic=topic,
                                                            human_analyst_feedback=human_analyst_feedback, 
                                                            max_analysts=max_analysts)

    # Generate question 
    analysts = structured_llm.invoke([SystemMessage(content=system_message)]+[HumanMessage(content="Génère l'ensemble des analystes.")])
    
    # Write the list of analysis to state
    return {"analysts": analysts.analysts}

### Nodes and edges
analyst_instructions="""Vous êtes chargé de créer un ensemble de personnalités d'analystes IA. Suivez ces instructions attentivement :

1. D'abord, examinez le sujet de recherche :
{topic}
        
2. Examinez les retours éditoriaux qui ont été éventuellement fournis pour guider la création des analystes : 
        
{human_analyst_feedback}
    
3. Déterminez les thèmes les plus intéressants basés sur les documents et/ou les retours ci-dessus.
                    
4. Sélectionnez les {max_analysts} meilleurs thèmes.

5. Assignez un analyste à chaque thème."""


def human_feedback(state: GenerateAnalystsState):
    """ No-op node that should be interrupted on """
    pass

# Generate analyst question
question_instructions = """Vous êtes un analyste chargé d'interviewer un expert pour en apprendre davantage sur un sujet spécifique.

Votre objectif est d'obtenir des insights intéressants et spécifiques liés à votre sujet.

1. Intéressants : Des insights que les gens trouveront surprenants ou non évidents.
        
2. Spécifiques : Des insights qui évitent les généralités et incluent des exemples concrets de l'expert.

Voici votre sujet de focus et vos objectifs : {goals}
        
Commencez par vous présenter en utilisant un nom qui correspond à votre personnalité, puis posez votre question.

Continuez à poser des questions pour approfondir et affiner votre compréhension du sujet.
        
Lorsque vous êtes satisfait de votre compréhension, terminez l'entretien par : "Merci beaucoup pour votre aide !"

N'oubliez pas de rester dans votre personnage tout au long de votre réponse, reflétant la personnalité et les objectifs qui vous ont été fournis."""

def generate_question(state: InterviewState):

    """ Node to generate a question """

    # Get state
    analyst = state["analyst"]
    messages = state["messages"]

    # Generate question 
    system_message = question_instructions.format(goals=analyst.persona)
    question = llm.invoke([SystemMessage(content=system_message)]+messages)
        
    # Write messages to state
    return {"messages": [question]}

# Search query writing
search_instructions = SystemMessage(content="""On vous donne une conversation entre un analyste et un expert.

Votre objectif est de générer une requête bien structurée pour la recherche et/ou la recherche web liée à la conversation.
        
D'abord, analysez la conversation complète.

Portez une attention particulière à la dernière question posée par l'analyste.

Convertissez cette dernière question en une requête de recherche web bien structurée.""")

def search_web(state: InterviewState):
    
    """ Retrieve docs from web search """

    # Search
    tavily_search = TavilySearchResults(max_results=3)

    # Search query
    structured_llm = llm.with_structured_output(SearchQuery)
    search_query = structured_llm.invoke([search_instructions]+state['messages'])
    
    # Search
    search_docs = tavily_search.invoke(search_query.search_query)

     # Format
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>'
            for doc in search_docs
        ]
    )

    return {"context": [formatted_search_docs]} 

def search_wikipedia(state: InterviewState):
    
    """ Retrieve docs from wikipedia """

    # Search query
    structured_llm = llm.with_structured_output(SearchQuery)
    search_query = structured_llm.invoke([search_instructions]+state['messages'])
    
    # Search
    search_docs = WikipediaLoader(query=search_query.search_query, 
                                  load_max_docs=2).load()

     # Format
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document source="{doc.metadata["source"]}" page="{doc.metadata.get("page", "")}"/>\n{doc.page_content}\n</Document>'
            for doc in search_docs
        ]
    )

    return {"context": [formatted_search_docs]} 

# Generate expert answer
answer_instructions = """Vous êtes un expert interviewé par un analyste.

Voici le domaine de focus de l'analyste : {goals}. 
        
Votre objectif est de répondre à une question posée par l'interviewer.

Pour répondre à la question, utilisez ce contexte :
        
{context}

Lors de vos réponses, suivez ces directives :
        
1. Utilisez uniquement les informations fournies dans le contexte. 
        
2. N'introduisez pas d'informations externes ou ne faites pas d'hypothèses au-delà de ce qui est explicitement indiqué dans le contexte.

3. Le contexte contient des sources au début de chaque document individuel.

4. Incluez ces sources dans votre réponse à côté de toute déclaration pertinente. Par exemple, pour la source #1, utilisez [1]. 

5. Listez vos sources dans l'ordre à la fin de votre réponse. [1] Source 1, [2] Source 2, etc.
        
6. Si la source est : <Document source="assistant/docs/llama3_1.pdf" page="7"/> alors listez simplement : 
        
[1] assistant/docs/llama3_1.pdf, page 7 
        
Et omettez l'ajout des crochets ainsi que le préambule Document source dans votre citation."""

def generate_answer(state: InterviewState):
    
    """ Node to answer a question """

    # Get state
    analyst = state["analyst"]
    messages = state["messages"]
    context = state["context"]

    # Answer question
    system_message = answer_instructions.format(goals=analyst.persona, context=context)
    answer = llm.invoke([SystemMessage(content=system_message)]+messages)
            
    # Name the message as coming from the expert
    answer.name = "expert"
    
    # Append it to state
    return {"messages": [answer]}

def save_interview(state: InterviewState):
    
    """ Save interviews """

    # Get messages
    messages = state["messages"]
    
    # Convert interview to a string
    interview = get_buffer_string(messages)
    
    # Save to interviews key
    return {"interview": interview}

def route_messages(state: InterviewState, 
                   name: str = "expert"):

    """ Route between question and answer """
    
    # Get messages
    messages = state["messages"]
    max_num_turns = state.get('max_num_turns',2)

    # Check the number of expert answers 
    num_responses = len(
        [m for m in messages if isinstance(m, AIMessage) and m.name == name]
    )

    # End if expert has answered more than the max turns
    if num_responses >= max_num_turns:
        return 'save_interview'

    # This router is run after each question - answer pair 
    # Get the last question asked to check if it signals the end of discussion
    last_question = messages[-2]
    
    if "Merci beaucoup pour votre aide" in last_question.content:
        return 'save_interview'
    return "ask_question"

# Write a summary (section of the final report) of the interview
section_writer_instructions = """Vous êtes un rédacteur technique expert.
            
Votre tâche est de créer une section courte et facilement digestible d'un rapport basée sur un ensemble de documents sources.

1. Analysez le contenu des documents sources : 
- Le nom de chaque document source est au début du document, avec la balise <Document.
        
2. Créez une structure de rapport en utilisant le formatage markdown :
- Utilisez ## pour le titre de la section
- Utilisez ### pour les sous-titres
        
3. Écrivez le rapport en suivant cette structure :
a. Titre (## header)
b. Résumé (### header)
c. Sources (### header)

4. Rendez votre titre engageant en fonction du domaine de focus de l'analyste : 
{focus}

5. Pour la section résumé :
- Commencez le résumé avec un contexte général/contexte lié au domaine de focus de l'analyste
- Mettez en valeur ce qui est nouveau, intéressant ou surprenant dans les insights recueillis lors de l'entretien
- Créez une liste numérotée des documents sources, au fur et à mesure que vous les utilisez
- Ne mentionnez pas les noms des interviewers ou des experts
- Viser environ 400 mots maximum
- Utilisez des sources numérotées dans votre rapport (ex: [1], [2]) basées sur les informations des documents sources
        
6. Dans la section Sources :
- Incluez toutes les sources utilisées dans votre rapport
- Fournissez des liens complets vers les sites web pertinents ou des chemins de documents spécifiques
- Séparez chaque source par un saut de ligne. Utilisez deux espaces à la fin de chaque ligne pour créer un saut de ligne en Markdown.
- Cela ressemblera à :

### Sources
[1] Lien ou nom du document
[2] Lien ou nom du document

7. Assurez-vous de combiner les sources. Par exemple, ceci n'est pas correct :

[3] https://ai.meta.com/blog/meta-llama-3-1/
[4] https://ai.meta.com/blog/meta-llama-3-1/

Il ne devrait pas y avoir de sources redondantes. Cela devrait simplement être :

[3] https://ai.meta.com/blog/meta-llama-3-1/
        
8. Révision finale :
- Assurez-vous que le rapport suit la structure requise
- N'incluez pas de préambule avant le titre du rapport
- Vérifiez que toutes les directives ont été suivies"""

def write_section(state: InterviewState):

    """ Node to write a section """

    # Get state
    interview = state["interview"]
    context = state["context"]
    analyst = state["analyst"]
   
    # Write section using either the gathered source docs from interview (context) or the interview itself (interview)
    system_message = section_writer_instructions.format(focus=analyst.description)
    section = llm.invoke([SystemMessage(content=system_message)]+[HumanMessage(content=f"Utilisez cette source pour écrire votre section : {context}")]) 
                
    # Append it to state
    return {"sections": [section.content]}

# Add nodes and edges 
interview_builder = StateGraph(InterviewState)
interview_builder.add_node("ask_question", generate_question)
interview_builder.add_node("search_web", search_web)
interview_builder.add_node("search_wikipedia", search_wikipedia)
interview_builder.add_node("answer_question", generate_answer)
interview_builder.add_node("save_interview", save_interview)
interview_builder.add_node("write_section", write_section)

# Flow
interview_builder.add_edge(START, "ask_question")
interview_builder.add_edge("ask_question", "search_web")
interview_builder.add_edge("ask_question", "search_wikipedia")
interview_builder.add_edge("search_web", "answer_question")
interview_builder.add_edge("search_wikipedia", "answer_question")
interview_builder.add_conditional_edges("answer_question", route_messages,['ask_question','save_interview'])
interview_builder.add_edge("save_interview", "write_section")
interview_builder.add_edge("write_section", END)

def initiate_all_interviews(state: ResearchGraphState):

    """ Conditional edge to initiate all interviews via Send() API or return to create_analysts """    

    # Check if human feedback
    human_analyst_feedback=state.get('human_analyst_feedback','approve')
    if human_analyst_feedback.lower() != 'approve':
        # Return to create_analysts
        return "create_analysts"

    # Otherwise kick off interviews in parallel via Send() API
    else:
        topic = state["topic"]
        return [Send("conduct_interview", {"analyst": analyst,
                                           "messages": [HumanMessage(
                                               content=f"Alors, vous avez dit que vous écriviez un article sur {topic} ?"
                                           )
                                                       ]}) for analyst in state["analysts"]]

# Write a report based on the interviews
report_writer_instructions = """Vous êtes un rédacteur technique créant un rapport sur ce sujet global : 

{topic}
    
Vous avez une équipe d'analystes. Chaque analyste a fait deux choses : 

1. Ils ont mené un entretien avec un expert sur un sous-sujet spécifique.
2. Ils ont rédigé leurs conclusions dans un mémo.

Votre tâche : 

1. On vous donnera une collection de memos de vos analystes.
2. Réfléchissez attentivement aux insights de chaque memo.
3. Consolidez-les en un résumé global concis qui relie les idées centrales de tous les memos.
4. Résumez les points centraux de chaque memo en un récit cohérent.

Pour formater votre rapport :
 
1. Utilisez le formatage markdown. 
2. N'incluez pas de préambule pour le rapport.
3. N'utilisez pas de sous-titre. 
4. Commencez votre rapport avec un seul titre d'en-tête : ## Insights
5. Ne mentionnez pas les noms des analystes dans votre rapport.
6. Préservez toutes les citations dans les memos, qui seront annotées entre crochets, par exemple [1] ou [2].
7. Créez une liste finale consolidée des sources et ajoutez-la à une section Sources avec l'en-tête `## Sources`.
8. Listez vos sources dans l'ordre et ne les répétez pas.

[1] Source 1
[2] Source 2

Voici les memos de vos analystes pour construire votre rapport : 

{context}"""

def write_report(state: ResearchGraphState):

    """ Node to write the final report body """

    # Full set of sections
    sections = state["sections"]
    topic = state["topic"]

    # Concat all sections together
    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])
    
    # Summarize the sections into a final report
    system_message = report_writer_instructions.format(topic=topic, context=formatted_str_sections)    
    report = llm.invoke([SystemMessage(content=system_message)]+[HumanMessage(content=f"Écrivez un rapport basé sur ces memos.")]) 
    return {"content": report.content}

# Write the introduction or conclusion
intro_conclusion_instructions = """Vous êtes un rédacteur technique finalisant un rapport sur {topic}

On vous donnera toutes les sections du rapport.

Votre travail est d'écrire une section d'introduction ou de conclusion concise et convaincante.

L'utilisateur vous indiquera s'il faut écrire l'introduction ou la conclusion.

N'incluez pas de préambule pour l'une ou l'autre section.

Ciblez environ 100 mots, prévisualisant brièvement (pour l'introduction) ou récapitulant (pour la conclusion) toutes les sections du rapport.

Utilisez le formatage markdown. 

Pour votre introduction, créez un titre convaincant et utilisez l'en-tête # pour le titre.

Pour votre introduction, utilisez ## Introduction comme en-tête de section. 

Pour votre conclusion, utilisez ## Conclusion comme en-tête de section.

Voici les sections sur lesquelles réfléchir pour l'écriture : {formatted_str_sections}"""

def write_introduction(state: ResearchGraphState):

    """ Node to write the introduction """

    # Full set of sections
    sections = state["sections"]
    topic = state["topic"]

    # Concat all sections together
    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])
    
    # Summarize the sections into a final report
    
    instructions = intro_conclusion_instructions.format(topic=topic, formatted_str_sections=formatted_str_sections)    
    intro = llm.invoke([instructions]+[HumanMessage(content=f"Écrivez l'introduction du rapport")]) 
    return {"introduction": intro.content}

def write_conclusion(state: ResearchGraphState):

    """ Node to write the conclusion """

    # Full set of sections
    sections = state["sections"]
    topic = state["topic"]

    # Concat all sections together
    formatted_str_sections = "\n\n".join([f"{section}" for section in sections])
    
    # Summarize the sections into a final report
    
    instructions = intro_conclusion_instructions.format(topic=topic, formatted_str_sections=formatted_str_sections)    
    conclusion = llm.invoke([instructions]+[HumanMessage(content=f"Écrivez la conclusion du rapport")]) 
    return {"conclusion": conclusion.content}

def finalize_report(state: ResearchGraphState):

    """ The is the "reduce" step where we gather all the sections, combine them, and reflect on them to write the intro/conclusion """

    # Save full final report
    content = state["content"]
    if content.startswith("## Insights"):
        content = content.strip("## Insights")
    if "## Sources" in content:
        try:
            content, sources = content.split("\n## Sources\n")
        except:
            sources = None
    else:
        sources = None

    final_report = state["introduction"] + "\n\n---\n\n" + content + "\n\n---\n\n" + state["conclusion"]
    if sources is not None:
        final_report += "\n\n## Sources\n" + sources
    return {"final_report": final_report}

# Add nodes and edges 
builder = StateGraph(ResearchGraphState)
builder.add_node("parse_initial_message", parse_initial_message)
builder.add_node("create_analysts", create_analysts)
builder.add_node("human_feedback", human_feedback)
builder.add_node("conduct_interview", interview_builder.compile())
builder.add_node("write_report",write_report)
builder.add_node("write_introduction",write_introduction)
builder.add_node("write_conclusion",write_conclusion)
builder.add_node("finalize_report",finalize_report)

# Logic
builder.add_edge(START, "parse_initial_message")
builder.add_edge("parse_initial_message", "create_analysts")
builder.add_edge("create_analysts", "human_feedback")
builder.add_conditional_edges("human_feedback", initiate_all_interviews, ["create_analysts", "conduct_interview"])
builder.add_edge("conduct_interview", "write_report")
builder.add_edge("conduct_interview", "write_introduction")
builder.add_edge("conduct_interview", "write_conclusion")
builder.add_edge(["write_conclusion", "write_report", "write_introduction"], "finalize_report")
builder.add_edge("finalize_report", END)

# Compile
graph = builder.compile(interrupt_before=['human_feedback'])