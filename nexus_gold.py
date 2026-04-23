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
    decision_prompt = f"Needs SQL? User: '{user_input}'. Respond JSON: {{\"sql_needed\": true/false}}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a JSON classifier."}, {"role": "user", "content": decision_prompt}],
        response_format={"type": "json_object"}
    )
    decision = json.loads(response.choices[0].message.content)
    
    if decision.get("sql_needed"):
        sql_prompt = f"Generate SQL for: '{user_input}'. Respond ONLY SQL."
        sql_res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Output ONLY raw SQL."}, {"role": "user", "content": sql_prompt}]
        ).choices[0].message.content.strip()
        sql_res = sql_res.replace("```sql", "").replace("```", "").strip()
        db_res = query_db(sql_res)
        final_prompt = f"Summarize results: {db_res} for: {user_input}"
        messages = [{"role": "system", "content": "You are NEXUS Agent. Use icons in response if helpful."}]
        messages.extend(history[-20:])
        messages.append({"role": "user", "content": final_prompt})
    else:
        messages = [{"role": "system", "content": "You are NEXUS Agent. A friendly AI with deep memory."}]
        messages.extend(history[-30:])
        messages.append({"role": "user", "content": user_input})

    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS GOLD PRO", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #010409 !important; color: #ffffff !important; }
    
    .header-logo { font-size: 2rem; font-weight: 800; color: #ffffff; margin-bottom: 25px; }
    .header-logo span { color: #c084fc; }
    
    .chat-container { display: flex; align-items: flex-start; margin-bottom: 20px; width: 100%; }
    .user-msg { justify-content: flex-end; }
    
    .bubble { padding: 12px 20px; border-radius: 20px; max-width: 80%; line-height: 1.6; position: relative; }
    .bubble-user { background: #7e22ce; color: white; border-radius: 20px 20px 0 20px; margin-left: auto; }
    .bubble-ai { background: #1e293b; color: #f1f5f9; border: 1px solid rgba(255,255,255,0.05); border-radius: 20px 20px 20px 0; }
    
    .avatar-ai { width: 35px; height: 35px; background: #fbbf24; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 1.2rem; }
    
    .stChatInputContainer { background-color: #010409 !important; border: 1px solid #1e293b !important; border-radius: 20px !important; }
    [data-testid="stSidebar"] { background: #010409 !important; border-right: 1px solid #1e293b; }
    
    .feature-card { padding: 15px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 15px; }
    
    header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#c084fc; font-weight:800; margin-top:20px;'>NEXUS PRO</h2>", unsafe_allow_html=True)
    mode = st.radio("Navigation", ["💬 Chat Terminal", "🏗️ Architecture", "✨ Key Features"])
    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.messages = []; st.rerun()
    st.markdown("---")
    st.caption("AI Status: Online")

# --- MAIN CONTENT ---
if mode == "💬 Chat Terminal":
    c_left, c_right = st.columns([1.1, 0.9])
    
    with c_right:
        st.markdown("#### 🕸️ Knowledge Graph")
        nodes = [Node(id="Nexus", label="NEXUS AI", color="#c084fc", size=30), Node(id="User", label="Amina", color="#818cf8", size=25)]
        edges = [Edge(source="User", target="Nexus", label="Interacts", color="#30363d")]
        config = Config(width=500, height=450, directed=True, backgroundColor="#010409")
        agraph(nodes=nodes, edges=edges, config=config)

    with c_left:
        st.markdown("<div class='header-logo'>⚡ <span>NEXUS</span> GOLD</div>", unsafe_allow_html=True)
        if "messages" not in st.session_state: st.session_state.messages = []
        
        chat_box = st.container(height=500)
        with chat_box:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f"<div class='chat-container user-msg'><div class='bubble bubble-user'>{msg['content']}</div></div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-container'><div class='avatar-ai'>🤖</div><div class='bubble bubble-ai'>{msg['content']}</div></div>", unsafe_allow_html=True)

        if prompt := st.chat_input("Message NEXUS..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_p = st.session_state.messages[-1]["content"]
        with chat_box:
            stream = nex_ai_core(last_p, st.session_state.messages[:-1])
            f_res = ""; r_box = st.empty()
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    f_res += chunk.choices[0].delta.content
                    r_box.markdown(f"<div class='chat-container'><div class='avatar-ai'>🤖</div><div class='bubble bubble-ai'>{f_res}▌</div></div>", unsafe_allow_html=True)
            r_box.markdown(f"<div class='chat-container'><div class='avatar-ai'>🤖</div><div class='bubble bubble-ai'>{f_res}</div></div>", unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": f_res})
            st.rerun()

elif mode == "🏗️ Architecture":
    st.markdown("### 🏗️ System Architecture")
    st.mermaid("graph TD; User-->NEXUS; NEXUS-->LLM; NEXUS-->DB")

else:
    st.markdown("### ✨ Key Features")
    st.markdown("<div class='feature-card'><b>Memory Engine</b>: 30-message context window.</div>", unsafe_allow_html=True)
    st.markdown("<div class='feature-card'><b>SQL Agent</b>: Real-time inventory queries.</div>", unsafe_allow_html=True)
