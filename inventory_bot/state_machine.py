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
    prompt = f"Identify if the user wants to 'query' the inventory database or just 'chitchat'. User Input: {state['user_input']}. Respond in JSON format: {{\"intent\": \"query\" or \"chitchat\"}}"
    res = llm.generate_json(prompt)
    try:
        intent_data = json.loads(res)
        return {**state, "intent": intent_data.get('intent', 'chitchat')}
    except:
        return {**state, "intent": "chitchat"}

def sql_generator(state: AgentState):
    schema = """
    Tables: Assets (id, name, quantity, status, category_id, vendor_id, location_id)
    """
    prompt = f"Generate a SQLite query for: {state['user_input']}. Schema: {schema}. Respond ONLY with SQL."
    query = llm.generate(prompt, system_instruction="You are a SQL generator. Output ONLY raw SQL code.")
    query = query.replace("```sql", "").replace("```", "").strip()
    return {**state, "sql_query": query}

def sql_executor(state: AgentState):
    res = execute_query(state['sql_query'])
    if "error" in res: return {**state, "error": res['error'], "query_results": None}
    return {**state, "query_results": res, "error": ""}

def sql_corrector(state: AgentState):
    if not state['error'] or state['retry_count'] >= 2: return state
    prompt = f"Fix this SQL: {state['sql_query']}. Error: {state['error']}."
    corrected = llm.generate(prompt, system_instruction="Fix SQL errors and output ONLY the corrected SQL.")
    return {**state, "sql_query": corrected.strip(), "retry_count": state['retry_count'] + 1}

def responder(state: AgentState):
    if state['intent'] == 'chitchat':
        res = llm.generate(state['user_input'])
    elif state['error']:
        res = f"I couldn't find that in the database. Error: {state['error']}"
    else:
        prompt = f"Summarize these inventory results for the user: {json.dumps(state['query_results'])}. User asked: {state['user_input']}"
        res = llm.generate(prompt)
    
    return {**state, "response": res}

# Graph setup
workflow = StateGraph(AgentState)
workflow.add_node("intent", intent_classifier); workflow.add_node("generator", sql_generator)
workflow.add_node("executor", sql_executor); workflow.add_node("corrector", sql_corrector)
workflow.add_node("responder", responder)

workflow.set_entry_point("intent")
workflow.add_conditional_edges("intent", lambda x: "responder" if x['intent'] == 'chitchat' else "generator")
workflow.add_edge("generator", "executor")
workflow.add_conditional_edges("executor", lambda x: "corrector" if x['error'] and x['retry_count'] < 2 else "responder")
workflow.add_edge("corrector", "executor")
workflow.add_edge("responder", END)

inventory_app = workflow.compile()
