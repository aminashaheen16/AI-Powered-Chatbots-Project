import json
from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
from shared.llm_client import LLMClient
from knowledge_bot.graph_db import GraphDB

class GraphState(TypedDict):
    user_input: str
    intent: str  # add, inquire, edit, delete
    entities: List[dict]
    cypher_query: str
    results: Union[list, dict, None]
    error: str
    response: str
    retry_count: int

llm = LLMClient()
db = GraphDB()

def graph_intent_classifier(state: GraphState):
    prompt = f"""
    Classify the intent for a Graph Database assistant.
    Input: {state['user_input']}
    
    Categories:
    - 'add': Creating new nodes or relationships (e.g., "Add Ahmed who works at Orange")
    - 'inquire': Querying existing data (e.g., "Who works at Orange?")
    - 'edit': Updating properties (e.g., "Change Ahmed's age to 25")
    - 'delete': Removing data (e.g., "Delete Ahmed")
    
    Respond in JSON: {{"intent": "add" | "inquire" | "edit" | "delete"}}
    """
    res = llm.generate_json(prompt)
    data = json.loads(res)
    return {**state, "intent": data.get('intent', 'inquire')}

def cypher_generator(state: GraphState):
    # Improved schema-aware prompt for paragraph handling
    schema = """
    Nodes: Person {name, age, position}, Organization {name, location}, Project {name, status}
    Relationships: (Person)-[:WORKS_AT]->(Organization), (Person)-[:WORKS_ON]->(Project)
    """
    
    prompt = f"""
    Generate a Neo4j Cypher query based on the intent '{state['intent']}'.
    Schema: {schema}
    User Input: {state['user_input']}
    
    Rules:
    - Use MERGE for adding to prevent duplicates.
    - Handle complex relationships mentioned in the text.
    - Respond ONLY with the Cypher query.
    """
    query = llm.generate(prompt, system_instruction="You are a Cypher expert. Output ONLY raw Cypher code.")
    query = query.replace("```cypher", "").replace("```", "").strip()
    return {**state, "cypher_query": query}

def cypher_executor(state: GraphState):
    try:
        results = db.execute_query(state['cypher_query'])
        return {**state, "results": results, "error": ""}
    except Exception as e:
        return {**state, "error": str(e), "results": None}

def cypher_corrector(state: GraphState):
    if not state['error'] or state['retry_count'] >= 2: return state
    prompt = f"Fix this Cypher query: {state['cypher_query']}. Error: {state['error']}."
    corrected = llm.generate(prompt, system_instruction="Fix Cypher syntax and output ONLY the corrected query.")
    return {**state, "cypher_query": corrected.strip(), "retry_count": state['retry_count'] + 1}

def graph_responder(state: GraphState):
    if state['error']:
        res = f"Graph Operation Failed: {state['error']}"
    else:
        prompt = f"Summarize these Graph results: {json.dumps(state['results'])}. Original Request: {state['user_input']}"
        res = llm.generate(prompt)
    return {**state, "response": res}

# Build Graph
workflow = StateGraph(GraphState)
workflow.add_node("classifier", graph_intent_classifier)
workflow.add_node("generator", cypher_generator)
workflow.add_node("executor", cypher_executor)
workflow.add_node("corrector", cypher_corrector)
workflow.add_node("responder", graph_responder)

workflow.set_entry_point("classifier")
workflow.add_edge("classifier", "generator")
workflow.add_edge("generator", "executor")
workflow.add_conditional_edges("executor", lambda x: "corrector" if x['error'] and x['retry_count'] < 2 else "responder")
workflow.add_edge("corrector", "executor")
workflow.add_edge("responder", END)

knowledge_graph_app = workflow.compile()
