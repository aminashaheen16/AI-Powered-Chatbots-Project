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

# --- AI CORE ---
def nex_ai_core(user_input, history):
    decision_prompt = f"Categorize: '{user_input}'. Intent: ADD/INQUIRE/EDIT/DELETE/CHAT. Needs SQL: true/false. Respond JSON."
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a JSON classifier."}, {"role": "user", "content": decision_prompt}],
        response_format={"type": "json_object"}
    )
    decision = json.loads(response.choices[0].message.content)
    intent = decision.get("intent", "CHAT")
    
    if decision.get("needs_sql"):
        sql_prompt = f"Generate SQL for: '{user_input}'. Respond ONLY SQL."
        sql_res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Output ONLY raw SQL."}, {"role": "user", "content": sql_prompt}]
        ).choices[0].message.content.strip()
        sql_res = sql_res.replace("```sql", "").replace("```", "").strip()
        db_res = query_db(sql_res)
        final_prompt = f"Summarize: {db_res} for: {user_input}"
        messages = [{"role": "system", "content": "You are NEXUS Agent."}]
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": final_prompt})
    else:
        messages = [{"role": "system", "content": "You are NEXUS Agent."}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": user_input})

    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True), intent

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS ULTIMATE AGENT", page_icon="🤖", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #010409; color: #ffffff !important; }
    .status-bar { display: flex; justify-content: flex-end; padding: 10px; gap: 15px; font-size: 0.75rem; }
    .status-pill { padding: 4px 12px; border-radius: 20px; background: rgba(16, 185, 129, 0.05); border: 1px solid #10b981; color: #10b981; font-weight: 600; }
    
    .chat-bubble-user { background: #7e22ce; padding: 15px 20px; border-radius: 20px 20px 0 20px; margin-bottom: 5px; margin-left: auto; max-width: 85%; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
    .chat-bubble-ai { background: #161b22; padding: 15px 20px; border-radius: 20px 20px 20px 0; margin-bottom: 5px; max-width: 85%; border: 1px solid #30363d; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
    
    .intent-badge { font-size: 0.65rem; font-weight: 800; padding: 2px 10px; border-radius: 6px; margin-bottom: 25px; display: inline-block; text-transform: uppercase; }
    .badge-add { background: #238636; color: white; }
    .badge-inquire { background: #1f6feb; color: white; }
    .badge-edit { background: #d29922; color: white; }
    .badge-delete { background: #da3633; color: white; }
    .badge-chat { background: #484f58; color: white; }
    
    .graph-container { background: #0d1117; border-radius: 20px; border: 1px solid #30363d; padding: 20px; margin-top: 20px; }
    [data-testid="stSidebar"] { background: #0d1117 !important; border-right: 1px solid #30363d !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR & STATUS ---
with st.sidebar:
    st.markdown("<h2 style='color:#c084fc; font-weight:800;'>NEXUS AGENT</h2>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🗑️ New Session", use_container_width=True):
        st.session_state.messages = []; st.rerun()

st.markdown("<div class='status-bar'><div class='status-pill'>● SQL Live</div><div class='status-pill' style='color:#818cf8; border-color:#818cf8;'>● Llama 3.3</div></div>", unsafe_allow_html=True)

# --- MAIN LAYOUT ---
col_chat, col_vis = st.columns([1.1, 0.9])

with col_vis:
    st.markdown("#### 🕸️ Graph Universe")
    with st.container():
        st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
        nodes = [Node(id="Amina", label="User: Amina", color="#c084fc", size=30), Node(id="Nexus", label="AI: Nexus", color="#818cf8", size=30)]
        edges = [Edge(source="Amina", target="Nexus", label="Interacts", color="#30363d")]
        config = Config(width=600, height=450, directed=True, nodeHighlightBehavior=True, highlightColor="#c084fc", backgroundColor="#0d1117")
        agraph(nodes=nodes, edges=edges, config=config)
        st.markdown("</div>", unsafe_allow_html=True)

with col_chat:
    st.markdown("#### 💬 AI Interface")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_box = st.container(height=500)
    with chat_box:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-bubble-ai'>{msg['content']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='intent-badge badge-{msg.get('intent','chat').lower()}'>{msg.get('intent','CHAT')}</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Enter command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_p = st.session_state.messages[-1]["content"]
        with chat_box:
            stream, intent = nex_ai_core(last_p, st.session_state.messages[:-1])
            f_res = ""; r_box = st.empty()
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    f_res += chunk.choices[0].delta.content
                    r_box.markdown(f"<div class='chat-bubble-ai'>{f_res}▌</div>", unsafe_allow_html=True)
            r_box.markdown(f"<div class='chat-bubble-ai'>{f_res}</div><div class='intent-badge badge-{intent.lower()}'>{intent}</div>", unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": f_res, "intent": intent})
            st.rerun()
