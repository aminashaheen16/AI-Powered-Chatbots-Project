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

def main_agent(state: AgentState):
    # Determine if it's a database query or general chat
    prompt = f"Decide if this user request needs a database query about inventory/assets: '{state['user_input']}'. Respond in JSON: {{\"needs_db\": true/false}}"
    decision = llm.generate_json(prompt)
    try:
        needs_db = json.loads(decision).get('needs_db', False)
    except:
        needs_db = False
        
    if not needs_db:
        # Direct response for general chat
        res = llm.generate(state['user_input'])
        return {**state, "response": res, "intent": "chitchat"}
    else:
        # Proceed to SQL generation
        return {**state, "intent": "query"}

def sql_generator(state: AgentState):
    if state['intent'] == 'chitchat': return state
    schema = "Table: Assets (name, quantity, status, category_id, vendor_id, location_id)"
    prompt = f"Generate SQL for: {state['user_input']}. Schema: {schema}"
    query = llm.generate(prompt, system_instruction="Output ONLY raw SQL.")
    return {**state, "sql_query": query.strip()}

def sql_executor(state: AgentState):
    if state['intent'] == 'chitchat': return state
    res = execute_query(state['sql_query'])
    return {**state, "query_results": res, "error": res.get('error', "")}

def responder(state: AgentState):
    if state['intent'] == 'chitchat': return state
    prompt = f"Summarize inventory data: {json.dumps(state['query_results'])} for request: {state['user_input']}"
    res = llm.generate(prompt)
    return {**state, "response": res}

# Simple Graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", main_agent)
workflow.add_node("generator", sql_generator)
workflow.add_node("executor", sql_executor)
workflow.add_node("responder", responder)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", lambda x: "generator" if x['intent'] == "query" else "responder")
workflow.add_edge("generator", "executor")
workflow.add_edge("executor", "responder")
workflow.add_edge("responder", END)

inventory_app = workflow.compile()
