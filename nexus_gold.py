import streamlit as st
import os
import sqlite3
import json
import time
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from streamlit_agraph import agraph, Node, Edge, Config

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

# --- AI CORE WITH INTENT TAGGING ---
def nex_ai_core(user_input, history):
    # Mapping intents like in the reference image
    decision_prompt = f"""
    Analyze the request: '{user_input}'.
    Categorize into one: 'ADD' (insert data), 'INQUIRE' (ask/query), 'EDIT' (update), 'DELETE' (remove), or 'CHAT' (general talk).
    Respond in JSON: {{"intent": "ADD"|"INQUIRE"|"EDIT"|"DELETE"|"CHAT", "needs_sql": true/false}}
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a JSON classifier."}, {"role": "user", "content": decision_prompt}],
        response_format={"type": "json_object"}
    )
    decision = json.loads(response.choices[0].message.content)
    intent = decision.get("intent", "CHAT")
    
    if decision.get("needs_sql"):
        sql_prompt = f"Generate SQLite for: '{user_input}'. Table: Assets (name, quantity, status). Respond ONLY with SQL."
        sql_res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Output ONLY raw SQL."}, {"role": "user", "content": sql_prompt}]
        ).choices[0].message.content.strip()
        
        sql_res = sql_res.replace("```sql", "").replace("```", "").strip()
        db_res = query_db(sql_res)
        
        final_prompt = f"Summarize inventory data: {db_res} for user request: {user_input}"
        messages = [{"role": "system", "content": "You are NEXUS, an inventory manager."}]
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": final_prompt})
    else:
        messages = [{"role": "system", "content": "You are NEXUS, a friendly assistant."}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": user_input})

    stream = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
    return stream, intent

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS KNOWLEDGE AGENT", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #020617; color: #ffffff !important; }
    .status-bar { display: flex; justify-content: flex-end; padding: 10px; gap: 15px; font-size: 0.8rem; }
    .status-pill { padding: 4px 12px; border-radius: 20px; background: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; color: #10b981; }
    .intent-badge { font-size: 0.65rem; font-weight: 800; padding: 2px 8px; border-radius: 4px; margin-top: 5px; display: inline-block; text-transform: uppercase; }
    .badge-add { background: #059669; color: white; }
    .badge-inquire { background: #2563eb; color: white; }
    .badge-edit { background: #d97706; color: white; }
    .badge-delete { background: #dc2626; color: white; }
    .badge-chat { background: #4b5563; color: white; }
    .chat-bubble-user { background: #7e22ce; padding: 12px 18px; border-radius: 18px 18px 0 18px; margin-bottom: 20px; margin-left: auto; max-width: 80%; }
    .chat-bubble-ai { background: rgba(30, 41, 59, 0.6); padding: 12px 18px; border-radius: 18px 18px 18px 0; margin-bottom: 5px; max-width: 80%; border: 1px solid rgba(255,255,255,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER STATUS ---
st.markdown("""
    <div class='status-bar'>
        <div class='status-pill'>● SQL Connected</div>
        <div class='status-pill' style='border-color:#818cf8; color:#818cf8;'>● Llama 3.3 Active</div>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#c084fc; font-weight:800;'>NEXUS AGENT</h1>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🗑️ New Session", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- MAIN CONTENT ---
col_left, col_right = st.columns([1.2, 0.8])

with col_right:
    st.markdown("#### 🕸️ Graph Intelligence")
    nodes = [Node(id="Amina", label="Amina", color="#c084fc"), Node(id="Nexus", label="Nexus", color="#818cf8")]
    edges = [Edge(source="Amina", target="Nexus", label="Controls", color="#ffffff")]
    agraph(nodes=nodes, edges=edges, config=Config(width=500, height=400, directed=True))

with col_left:
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            intent_class = f"badge-{msg.get('intent', 'chat').lower()}"
            st.markdown(f"<div class='chat-bubble-ai'>{msg['content']}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='intent-badge {intent_class}'>{msg.get('intent', 'CHAT')}</div><div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Command NEXUS Agent..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_prompt = st.session_state.messages[-1]["content"]
        with st.spinner("Processing..."):
            stream, intent = nex_ai_core(last_prompt, st.session_state.messages[:-1])
            full_res = ""; res_box = st.empty()
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_box.markdown(f"<div class='chat-bubble-ai'>{full_res}▌</div>", unsafe_allow_html=True)
            
            intent_class = f"badge-{intent.lower()}"
            res_box.markdown(f"<div class='chat-bubble-ai'>{full_res}</div><div class='intent-badge {intent_class}'>{intent}</div>", unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full_res, "intent": intent})
            st.rerun()
