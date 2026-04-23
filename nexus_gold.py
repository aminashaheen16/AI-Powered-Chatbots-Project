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

def get_stats():
    res = query_db("SELECT COUNT(*) FROM Assets")
    total = res['data'][0][0] if not res.get('error') else 0
    return total

# --- AI CORE WITH MEMORY ---
def nex_ai_core(user_input, history):
    decision_prompt = f"Does this need inventory data? User: '{user_input}'. Respond in JSON: {{\"sql_needed\": true/false}}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a JSON classifier."}, {"role": "user", "content": decision_prompt}],
        response_format={"type": "json_object"}
    )
    decision = json.loads(response.choices[0].message.content)
    
    if decision.get("sql_needed"):
        sql_prompt = f"Generate SQLite for: '{user_input}'. Table: Assets (name, quantity, status). Output ONLY raw SQL."
        sql_res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Output ONLY raw SQL."}, {"role": "user", "content": sql_prompt}]
        ).choices[0].message.content.strip()
        
        sql_res = sql_res.replace("```sql", "").replace("```", "").strip()
        db_res = query_db(sql_res)
        
        final_prompt = f"Summarize these results: {db_res} for the user. User asked: {user_input}"
        messages = [{"role": "system", "content": "You are NEXUS, an inventory expert."}]
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": final_prompt})
    else:
        messages = [{"role": "system", "content": "You are NEXUS, a friendly AI assistant with memory."}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": user_input})

    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS ULTIMATE", page_icon="🔱", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: radial-gradient(circle at top right, #1e1b4b, #020617); color: #ffffff !important; }
    .brand-text { font-size: 2.5rem; font-weight: 800; background: linear-gradient(45deg, #c084fc, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .stat-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 15px; text-align: center; }
    .chat-bubble-user { background: #7e22ce; padding: 12px 18px; border-radius: 18px 18px 0 18px; margin-bottom: 10px; margin-left: auto; max-width: 85%; font-size: 0.95rem; }
    .chat-bubble-ai { background: rgba(30, 41, 59, 0.6); padding: 12px 18px; border-radius: 18px 18px 18px 0; margin-bottom: 10px; max-width: 85%; border: 1px solid rgba(255,255,255,0.1); font-size: 0.95rem; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<div class='brand-text'>NEXUS AI</div>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🗑️ Reset Chat", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- TOP DASHBOARD ---
t_assets = get_stats()
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(f"<div class='stat-card'><div style='color:#94a3b8; font-size:0.7rem;'>ASSETS</div><div style='color:#c084fc; font-size:1.5rem; font-weight:800;'>{t_assets}</div></div>", unsafe_allow_html=True)
with c2: st.markdown("<div class='stat-card'><div style='color:#94a3b8; font-size:0.7rem;'>STATUS</div><div style='color:#4ade80; font-size:1.5rem; font-weight:800;'>ACTIVE</div></div>", unsafe_allow_html=True)
with c3: st.markdown("<div class='stat-card'><div style='color:#94a3b8; font-size:0.7rem;'>ENGINE</div><div style='color:#818cf8; font-size:1.5rem; font-weight:800;'>LLAMA 3</div></div>", unsafe_allow_html=True)
with c4: st.markdown("<div class='stat-card'><div style='color:#94a3b8; font-size:0.7rem;'>UPTIME</div><div style='color:#f472b6; font-size:1.5rem; font-weight:800;'>99%</div></div>", unsafe_allow_html=True)

st.markdown("---")

# --- MAIN CONTENT: Chat + Graph ---
col_left, col_right = st.columns([1.2, 0.8])

with col_right:
    st.markdown("### 🕸️ Knowledge Graph")
    nodes = [Node(id="Amina", label="Amina", color="#c084fc"), Node(id="Orange", label="Orange", color="#818cf8")]
    edges = [Edge(source="Amina", target="Orange", label="Works At", color="#ffffff")]
    config = Config(width=500, height=400, directed=True, nodeHighlightBehavior=True, staticGraph=False)
    agraph(nodes=nodes, edges=edges, config=config)

with col_left:
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state.messages:
            cls = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-ai"
            st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Message NEXUS..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # Handle response logic outside the input to avoid refresh issues
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_prompt = st.session_state.messages[-1]["content"]
        with chat_container:
            full_res = ""; res_box = st.empty()
            for chunk in nex_ai_core(last_prompt, st.session_state.messages[:-1]):
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_box.markdown(f"<div class='chat-bubble-ai'>{full_res}▌</div>", unsafe_allow_html=True)
            res_box.markdown(f"<div class='chat-bubble-ai'>{full_res}</div>", unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            st.rerun()
