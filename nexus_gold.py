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

# --- AI CORE WITH MEMORY ---
def nex_ai_core(user_input, history):
    # Phase 1: Determine if we need SQL
    decision_prompt = f"Does this need inventory data? User: '{user_input}'. Respond in JSON: {{\"sql_needed\": true/false}}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a JSON classifier."}, {"role": "user", "content": decision_prompt}],
        response_format={"type": "json_object"}
    )
    decision = json.loads(response.choices[0].message.content)
    
    if decision.get("sql_needed"):
        sql_prompt = f"Generate SQLite for: '{user_input}'. Table: Assets (name, quantity, status). Respond ONLY with SQL."
        sql_res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Output ONLY raw SQL."}, {"role": "user", "content": sql_prompt}]
        ).choices[0].message.content.strip()
        sql_res = sql_res.replace("```sql", "").replace("```", "").strip()
        db_res = query_db(sql_res)
        
        final_prompt = f"Summarize these inventory results: {db_res} for user: {user_input}"
        messages = [{"role": "system", "content": "You are NEXUS, an inventory expert."}]
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": final_prompt})
    else:
        messages = [{"role": "system", "content": "You are NEXUS, a friendly AI assistant with memory."}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": user_input})

    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS GOLD", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #020617; color: #ffffff !important; }
    
    .chat-bubble-user { background: #7e22ce; padding: 15px 25px; border-radius: 25px 25px 0 25px; margin-bottom: 20px; margin-left: auto; width: fit-content; max-width: 85%; }
    .chat-bubble-ai { background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255,255,255,0.1); padding: 15px 25px; border-radius: 25px 25px 25px 0; margin-bottom: 20px; width: fit-content; max-width: 85%; }
    
    [data-testid="stSidebar"] { background: #0f172a !important; }
    .stChatInputContainer { border-radius: 30px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#c084fc; font-weight:800;'>NEXUS GOLD</h1>", unsafe_allow_html=True)
    st.caption("v2.0 | Pure Edition")
    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []; st.rerun()

st.title("⚡ NEXUS GOLD")
st.caption("Simplified. Powerful. Direct.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display messages
for msg in st.session_state.messages:
    cls = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-ai"
    st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)

if prompt := st.chat_input("Ask NEXUS anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<div class='chat-bubble-user'>{prompt}</div>", unsafe_allow_html=True)

    with st.chat_message("assistant", avatar=None):
        full_res = ""; res_box = st.empty()
        for chunk in nex_ai_core(prompt, st.session_state.messages[:-1]):
            if chunk.choices[0].delta.content:
                full_res += chunk.choices[0].delta.content
                res_box.markdown(f"<div class='chat-bubble-ai'>{full_res}▌</div>", unsafe_allow_html=True)
        res_box.markdown(f"<div class='chat-bubble-ai'>{full_res}</div>", unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
