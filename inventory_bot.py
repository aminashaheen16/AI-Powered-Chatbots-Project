import sqlite3
import os
import json
from groq import Groq
from dotenv import load_dotenv

# --- CONFIG ---
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
DB_PATH = 'data/inventory.db'

# --- MEMORY MANAGEMENT ---

def save_memory(user_input, ai_response, session_id="default"):
    """Saves interaction to SQLite for long-term memory."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ChatHistory (session_id, user_input, ai_response) VALUES (?, ?, ?)",
                   (session_id, user_input, ai_response))
    conn.commit()
    conn.close()

def load_memory(session_id="default", limit=5):
    """Loads last few interactions for context."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_input, ai_response FROM ChatHistory WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
                   (session_id, limit))
    rows = cursor.fetchall()
    conn.close()
    # Reverse to keep chronological order
    return [{"user": r[0], "ai": r[1]} for r in reversed(rows)]

# --- STATE MACHINE NODES ---

def generator_node(user_input, history):
    """Generates SQL based on NL input and history."""
    prompt = f"""
    You are a SQL Generator for an Enterprise Inventory System.
    SCHEMA: Assets (id, name, quantity, status, vendor, location)
    
    CONVERSATION HISTORY:
    {history}
    
    BUSINESS RULES:
    1. By default, only query 'Active' records.
    2. Exclude 'Disposed' or 'Retired' assets from general counts.
    3. Return ONLY the raw SQL query. No explanation, no backticks.
    
    User Request: {user_input}
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a specialized SQL writer for SQLite."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip().replace("```sql", "").replace("```", "").strip()

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
    The following SQLite query failed:
    QUERY: {failed_query}
    ERROR: {error_message}
    
    Fix the query and return ONLY the corrected SQL. No markdown formatting.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a SQL debugging expert."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip().replace("```sql", "").replace("```", "").strip()

def responder_node(user_input, db_results):
    """Synthesizes the final NL response."""
    prompt = f"""
    User Input: {user_input}
    Database Results: {db_results}
    
    Translate the database results into a friendly, professional natural language response.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are NEXUS, a professional Inventory Assistant."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# --- EVALUATION NODE ---

def evaluation_node(user_input, sql_query, db_results, ai_response):
    """Evaluates the system performance for this turn."""
    prompt = f"""
    Evaluate this AI response:
    - User Input: {user_input}
    - SQL Query: {sql_query}
    - DB Results: {db_results}
    - AI Final Response: {ai_response}
    
    Return JSON: {{
        'accuracy_score': 0-10,
        'sql_correctness': boolean,
        'feedback': 'short comment'
    }}
    """
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant", # Use a smaller model for evaluation
        messages=[{"role": "system", "content": "You are a quality assurance agent."},
                  {"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# --- MAIN LOOP ---

def main():
    print("="*50)
    print("🔱 NEXUS INVENTORY BOT (SQL + MEMORY + EVAL)")
    print("="*50)
    
    # Load Long-Term Memory
    history = load_memory()
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit', 'bye']:
                break
            
            # 1. Intent Check
            intent_check = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "Identify if CHITCHAT or DB_QUERY. JSON: {'intent': '...'}"}],
                response_format={"type": "json_object"}
            )
            intent = json.loads(intent_check.choices[0].message.content).get("intent")
            
            if intent == "CHITCHAT":
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": "Respond to: " + user_input}]
                ).choices[0].message.content
                print(f"NEXUS: {res}")
                continue

            # 2. Workflow
            sql = generator_node(user_input, history)
            results = executor_node(sql)
            
            if results["status"] == "error":
                sql = corrector_node(sql, results["message"])
                results = executor_node(sql)
                
            if results["status"] == "success":
                answer = responder_node(user_input, results["data"])
                print(f"NEXUS: {answer}")
                
                # 3. Save Memory
                save_memory(user_input, answer)
                history.append({"user": user_input, "ai": answer})
                if len(history) > 5: history.pop(0) # Keep short-term window
                
                # 4. Evaluation (Background or Silent)
                eval_res = evaluation_node(user_input, sql, results["data"], answer)
                print(f"[EVAL] Accuracy: {eval_res['accuracy_score']}/10 | {eval_res['feedback']}")
            else:
                print(f"NEXUS: Persistent error - {results['message']}")
        except KeyboardInterrupt: break

if __name__ == "__main__":
    main()
