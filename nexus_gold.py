import streamlit as st
import os
import sqlite3
import json
import time
from groq import Groq
from dotenv import load_dotenv

# --- CONFIG & LOAD ---
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- DB HELPERS ---
def query_db(sql):
    try:
        conn = sqlite3.connect('data/inventory.db')
        cursor = conn.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        conn.close()
        return {"data": res, "cols": cols}
    except Exception as e:
        return {"error": str(e)}

# --- AI CORE ---
def nex_ai_core(user_input):
    # Phase 1: Determine if we need SQL
    decision_prompt = f"Does this need inventory data? User: '{user_input}'. Respond in JSON: {{\"sql_needed\": true/false}}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a JSON classifier."}, {"role": "user", "content": decision_prompt}],
        response_format={"type": "json_object"}
    )
    decision = json.loads(response.choices[0].message.content)
    
    if decision.get("sql_needed"):
        # Phase 2: Generate SQL
        sql_prompt = f"Generate SQLite for: '{user_input}'. Table: Assets (name, quantity, status). Output ONLY raw SQL."
        sql_res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Output ONLY raw SQL."}, {"role": "user", "content": sql_prompt}]
        ).choices[0].message.content.strip()
        
        # Clean SQL
        sql_res = sql_res.replace("```sql", "").replace("```", "").strip()
        db_res = query_db(sql_res)
        
        # Phase 3: Final Response
        final_prompt = f"Summarize these results: {db_res} for the user. User asked: {user_input}"
        final_res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "You are NEXUS, a helpful inventory expert."}, {"role": "user", "content": final_prompt}]
        ).choices[0].message.content.strip()
        return final_res
    else:
        # Direct Chat
        return client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "You are NEXUS, a friendly AI assistant."}, {"role": "user", "content": user_input}]
        ).choices[0].message.content.strip()

# --- STREAMLIT UI ---
st.set_page_config(page_title="NEXUS GOLD", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%) !important; color: white !important; }
    .stChatInputContainer { background-color: #1e293b !important; border-radius: 20px !important; }
    .stChatMessage { border-radius: 15px !important; margin-bottom: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ NEXUS GOLD EDITION")
st.caption("Simplified. Faster. Smarter.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask NEXUS anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = nex_ai_core(prompt)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
