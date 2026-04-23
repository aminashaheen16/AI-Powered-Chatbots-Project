import sqlite3
import os
import json
from groq import Groq
from dotenv import load_dotenv

# --- CONFIG ---
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
DB_PATH = 'data/inventory.db'

# --- STATE MACHINE NODES ---

def generator_node(user_input, history):
    """Generates SQL based on NL input."""
    prompt = f"""
    You are a SQL Generator for an Inventory System.
    SCHEMA: Assets (id, name, quantity, status, vendor, location)
    RULE: By default, only query 'Active' records unless asked otherwise.
    
    User Request: {user_input}
    Conversation History: {history}
    
    Return ONLY the raw SQL query. No explanation.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a specialized SQL writer."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def executor_node(sql_query):
    """Executes SQL and returns results or error."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        conn.close()
        return {"status": "success", "data": rows, "cols": cols}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def corrector_node(failed_query, error_message):
    """Self-corrects a failed SQL query."""
    print(f"\n[AI-CORRECTION] Detected error: {error_message}. Re-planning...")
    prompt = f"""
    The following SQL query failed:
    QUERY: {failed_query}
    ERROR: {error_message}
    
    Fix the query and return ONLY the corrected SQL.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a SQL debugging expert."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def responder_node(user_input, db_results):
    """Synthesizes the final NL response."""
    prompt = f"""
    User Input: {user_input}
    Database Results: {db_results}
    
    Translate the DB results into a friendly, professional natural language response.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are NEXUS, a professional Inventory Assistant."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# --- MAIN LOOP ---

def main():
    print("="*50)
    print("🔱 NEXUS INVENTORY BOT (SQL-CLI)")
    print("="*50)
    history = []
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("NEXUS: Goodbye!")
            break
        
        # 1. Intent Check (Chitchat vs Query)
        intent_check = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Identify if query is CHITCHAT or DB_QUERY. Return JSON: {'intent': '...'}"}],
            response_format={"type": "json_object"}
        )
        intent = json.loads(intent_check.choices[0].message.content).get("intent")
        
        if intent == "CHITCHAT":
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "Respond friendly to: " + user_input}]
            ).choices[0].message.content
            print(f"NEXUS: {res}")
            continue

        # 2. SQL Workflow
        sql = generator_node(user_input, history)
        results = executor_node(sql)
        
        # 3. Self-Correction Loop (One retry)
        if results["status"] == "error":
            sql = corrector_node(sql, results["message"])
            results = executor_node(sql)
            
        # 4. Respond
        if results["status"] == "success":
            answer = responder_node(user_input, results["data"])
            print(f"NEXUS: {answer}")
            history.append({"user": user_input, "ai": answer})
        else:
            print(f"NEXUS: I'm sorry, I encountered a persistent error: {results['message']}")

if __name__ == "__main__":
    main()
