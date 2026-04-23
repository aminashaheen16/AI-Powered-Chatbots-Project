import os
import json
from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
from shared.llm_client import LLMClient
from inventory_bot.database import execute_query

class AgentState(TypedDict):
    user_input: str
    intent: str
    sql_query: str
    query_results: Union[dict, None]
    error: str
    history: List[str]
    response: str
    retry_count: int

llm = LLMClient()

def intent_classifier(state: AgentState):
    prompt = f"""
    Classify the user input into 'chitchat' or 'query'.
    'chitchat': Greetings, personal questions, or general talk.
    'query': Questions about assets, inventory, vendors, locations, or database records.
    
    User Input: {state['user_input']}
    
    Respond in JSON format: {{"intent": "chitchat" | "query"}}
    """
    res = llm.generate_json(prompt)
    intent_data = json.loads(res)
    return {**state, "intent": intent_data['intent']}

def sql_generator(state: AgentState):
    schema = """
    Tables:
    - AssetCategories (id, name)
    - Vendors (id, name, contact)
    - Locations (id, name, address)
    - Assets (id, name, category_id, vendor_id, location_id, status, quantity)
    
    Business Rules:
    - Default to 'Active' status unless specified.
    - Exclude 'Disposed' or 'Retired' unless asked.
    """
    
    prompt = f"""
    Generate a valid SQLite query for the following request.
    Schema: {schema}
    User Request: {state['user_input']}
    
    Respond ONLY with the SQL query.
    """
    query = llm.generate(prompt)
    # Basic cleanup
    query = query.replace("```sql", "").replace("```", "").strip()
    return {**state, "sql_query": query}

def sql_executor(state: AgentState):
    res = execute_query(state['sql_query'])
    if "error" in res:
        return {**state, "error": res['error'], "query_results": None}
    return {**state, "query_results": res, "error": ""}

def sql_corrector(state: AgentState):
    if not state['error'] or state['retry_count'] >= 2:
        return state
    
    prompt = f"""
    The following SQL query failed with an error. Correct it.
    Query: {state['sql_query']}
    Error: {state['error']}
    
    Respond ONLY with the corrected SQL query.
    """
    corrected_query = llm.generate(prompt)
    corrected_query = corrected_query.replace("```sql", "").replace("```", "").strip()
    return {**state, "sql_query": corrected_query, "retry_count": state['retry_count'] + 1}

def responder(state: AgentState):
    if state['intent'] == 'chitchat':
        prompt = f"Respond to this greeting or chitchat naturally: {state['user_input']}"
        res = llm.generate(prompt)
    elif state['error']:
        res = f"I'm sorry, I couldn't process your request. Error: {state['error']}"
    else:
        prompt = f"""
        Format the following database results into a natural language response.
        User Query: {state['user_input']}
        Results: {json.dumps(state['query_results'])}
        
        Respond naturally.
        """
        res = llm.generate(prompt)
    
    return {**state, "response": res}

# Building the Graph
workflow = StateGraph(AgentState)

workflow.add_node("intent", intent_classifier)
workflow.add_node("generator", sql_generator)
workflow.add_node("executor", sql_executor)
workflow.add_node("corrector", sql_corrector)
workflow.add_node("responder", responder)

workflow.set_entry_point("intent")

def route_intent(state: AgentState):
    if state['intent'] == 'chitchat':
        return "responder"
    return "generator"

def route_execution(state: AgentState):
    if state['error'] and state['retry_count'] < 2:
        return "corrector"
    return "responder"

workflow.add_conditional_edges("intent", route_intent)
workflow.add_edge("generator", "executor")
workflow.add_conditional_edges("executor", route_execution)
workflow.add_edge("corrector", "executor")
workflow.add_edge("responder", END)

inventory_app = workflow.compile()
