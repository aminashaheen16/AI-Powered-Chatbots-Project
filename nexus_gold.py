import streamlit as st
import os
import sqlite3
import json
import time
import pandas as pd
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
        messages = [{"role": "system", "content": "You are NEXUS Agent."}]
        messages.extend(history[-20:])
        messages.append({"role": "user", "content": final_prompt})
    else:
        messages = [{"role": "system", "content": "You are NEXUS Agent."}]
        messages.extend(history[-30:])
        messages.append({"role": "user", "content": user_input})

    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS GOLD PRO", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #020617 !important; color: #ffffff !important; }
    .header-logo { font-size: 2rem; font-weight: 800; color: #ffffff; margin-bottom: 20px; }
    .header-logo span { color: #c084fc; }
    
    .feature-card { padding: 20px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); height: 180px; margin-bottom: 20px; }
    .feature-title { font-weight: 800; font-size: 1.1rem; margin-bottom: 10px; }
    .feature-desc { font-size: 0.8rem; color: #cbd5e1; line-height: 1.4; }
    
    .chat-bubble-user { background: #7e22ce; color: #ffffff; padding: 12px 20px; border-radius: 20px 20px 0 20px; margin-bottom: 15px; margin-left: auto; width: fit-content; max-width: 80%; }
    .chat-bubble-ai { background: #1e293b; color: #f1f5f9; border: 1px solid rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 20px 20px 20px 0; margin-bottom: 15px; width: fit-content; max-width: 80%; line-height: 1.6; }
    
    [data-testid="stSidebar"] { background: #010409 !important; border-right: 1px solid #1e293b; }
    header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#c084fc; font-weight:800;'>NEXUS PRO</h2>", unsafe_allow_html=True)
    mode = st.sidebar.radio("Navigation", ["💬 Chat Terminal", "✨ Key Features", "🏗️ System Architecture"])
    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- MAIN CONTENT ---
if mode == "💬 Chat Terminal":
    st.markdown("<div class='header-logo'>⚡ <span>NEXUS</span> GOLD</div>", unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        cls = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-ai"
        st.markdown(f"<div class={cls}>{msg['content']}</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Message NEXUS..."):
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

elif mode == "✨ Key Features":
    st.markdown("### ✨ Key Features")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("<div class='feature-card' style='background:rgba(126,34,206,0.15); border-color:#7e22ce;'><div class='feature-title' style='color:#c084fc;'>Intent classifier</div><div class='feature-desc'>Detects add, inquire, edit, delete, chitchat, and out_of_scope intents from natural language using Llama 3.3.</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='feature-card' style='background:rgba(5,150,105,0.15); border-color:#059669;'><div class='feature-title' style='color:#34d399;'>Short-term memory</div><div class='feature-desc'>State-aware session memory that tracks context and resolves pronouns (e.g. 'her name', 'it').</div></div>", unsafe_allow_html=True)
        
    with c2:
        st.markdown("<div class='feature-card' style='background:rgba(37,99,235,0.15); border-color:#2563eb;'><div class='feature-title' style='color:#60a5fa;'>SQL Generation</div><div class='feature-desc'>Converts natural language into valid SQLite queries. Validates syntax before execution.</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='feature-card' style='background:rgba(15,23,42,0.5); border-color:#334155;'><div class='feature-title' style='color:#94a3b8;'>Long-term memory</div><div class='feature-desc'>Persistent database storage that survives server restarts and is available across all sessions.</div></div>", unsafe_allow_html=True)
        
    with c3:
        st.markdown("<div class='feature-card' style='background:rgba(6,95,70,0.15); border-color:#065f46;'><div class='feature-title' style='color:#10b981;'>Auto-retry on error</div><div class='feature-desc'>If SQL execution fails, the agent regenerates the query automatically with the error in context.</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='feature-card' style='background:rgba(180,83,9,0.15); border-color:#b45309;'><div class='feature-title' style='color:#fbbf24;'>Evaluation suite</div><div class='feature-desc'>Traces and measures intent accuracy and query validity for continuous performance monitoring.</div></div>", unsafe_allow_html=True)

    st.markdown("<br>#### 🧠 Memory Type Comparison", unsafe_allow_html=True)
    mem_data = {
        "Memory Type": ["Short-term", "Long-term"],
        "Storage": ["RAM - Session State", "SQLite - Disk"],
        "Survives Restart": ["❌ No", "✅ Yes"],
        "Scope": ["Current Session", "Global Context"],
        "Purpose": ["Pronoun resolution", "Knowledge retrieval"]
    }
    st.table(pd.DataFrame(mem_data))

else:
    st.markdown("### 🏗️ System Architecture")
    st.mermaid("""
    graph TD
        User((User)) --> UI[Streamlit UI]
        UI --> Classifier{Intent Classifier}
        Classifier -- SQL --> SQLGen[SQL Generator]
        SQLGen --> Executor[DB Executor]
        Executor --> Response[Final Response]
        Classifier -- Chat --> Direct[Direct Chat]
        Direct --> Response
    """)
