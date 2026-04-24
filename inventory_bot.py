import sqlite3
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
DB_PATH = "data/inventory.db"

def load_memory(session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_input, ai_response FROM ChatHistory WHERE session_id = ? ORDER BY timestamp DESC LIMIT 5", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"user": r[0], "ai": r[1]} for r in rows[::-1]]

def save_memory(user_input, ai_response, session_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ChatHistory (session_id, user_input, ai_response) VALUES (?, ?, ?)", (session_id, user_input, ai_response))
    conn.commit()
    conn.close()

def generator_node(user_input, history):
    prompt = f"""
    System: You are an expert SQL Generator. Output ONLY raw SQL for SQLite.
    Schema: Assets(id, name, quantity, status, vendor, location). 
    Rule: Always filter by status='active' unless asked otherwise.
    Context: {history}
    User: {user_input}
    SQL:"""
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], stop=["\n"])
    return res.choices[0].message.content.strip()

def executor_node(sql):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql)
        cols = [d[0] for d in cursor.description]
        data = [dict(zip(cols, row)) for row in cursor.fetchall()]
        conn.close()
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def corrector_node(sql, error):
    prompt = f"The SQL query '{sql}' failed with error: {error}. Fix the SQL for SQLite and return ONLY the query."
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
    return res.choices[0].message.content.strip()

def responder_node(user_input, data):
    prompt = f"System: Use ONLY the provided data to answer. Do NOT hallucinate items. Data: {data}\nUser: {user_input}\nResponse:"
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
    return res.choices[0].message.content.strip()

def evaluation_node(user_input, sql, data, answer):
    prompt = f"""
    Auditor Task: Score the AI response (0-10) and give feedback.
    Input: {user_input}
    SQL used: {sql}
    Real DB Data: {data}
    AI Response: {answer}
    
    Rule: If the AI mentioned the items correctly from the Data, give a high score. Do NOT complain about missing items if they aren't in the Data.
    Return JSON: {{"accuracy_score": int, "feedback": str}}
    """
    res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
    return json.loads(res.choices[0].message.content)
