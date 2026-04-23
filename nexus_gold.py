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

def get_stats():
    try:
        conn = sqlite3.connect('data/inventory.db')
        c = conn.cursor()
        total = c.execute("SELECT COUNT(*) FROM Assets").fetchone()[0]
        active = c.execute("SELECT COUNT(*) FROM Assets WHERE status != 'Out of Stock'").fetchone()[0]
        low = c.execute("SELECT COUNT(*) FROM Assets WHERE quantity < 5").fetchone()[0]
        conn.close()
        return {"total": total, "active": active, "low": low}
    except:
        return {"total": 0, "active": 0, "low": 0}

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
        messages = [{"role": "system", "content": "You are NEXUS, an expert inventory agent."}]
        messages.extend(history[-25:])
        messages.append({"role": "user", "content": final_prompt})
    else:
        messages = [{"role": "system", "content": "You are NEXUS, a friendly AI assistant."}]
        messages.extend(history[-35:])
        messages.append({"role": "user", "content": user_input})

    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS ENTERPRISE", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #010409 !important; color: #ffffff !important; }
    
    /* Global Styles */
    .header-logo { font-size: 2.2rem; font-weight: 800; color: #ffffff; padding: 20px 0; }
    .header-logo span { color: #c084fc; }
    
    /* Metrics Cards */
    .metric-card { background: #161b22; border: 1px solid #30363d; border-radius: 15px; padding: 25px; text-align: center; }
    .metric-val { font-size: 2.5rem; font-weight: 800; color: #c084fc; }
    .metric-label { font-size: 0.9rem; color: #8b949e; margin-top: 5px; }
    
    /* Chat bubbles */
    .chat-container { display: flex; align-items: flex-start; margin-bottom: 25px; }
    .user-msg { justify-content: flex-end; }
    .bubble { padding: 15px 22px; border-radius: 20px; max-width: 85%; line-height: 1.6; }
    .bubble-user { background: #7e22ce; color: white; border-radius: 22px 22px 0 22px; margin-left: auto; }
    .bubble-ai { background: #1e293b; color: #f1f5f9; border: 1px solid rgba(255,255,255,0.05); border-radius: 22px 22px 22px 0; }
    .avatar-ai { width: 40px; height: 40px; background: #fbbf24; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-size: 1.3rem; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background: #010409 !important; border-right: 1px solid #1e293b; }
    .stButton > button { background-color: #7e22ce !important; color: white !important; border-radius: 12px !important; }
    
    header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#c084fc; font-weight:800; margin-top:20px;'>NEXUS PRO</h2>", unsafe_allow_html=True)
    mode = st.radio("Navigation", ["💬 Chat Terminal", "📈 Assets Dashboard", "🏗️ System Architecture", "✨ Key Features"])
    if st.button("＋ New Session", use_container_width=True):
        st.session_state.messages = []; st.rerun()
    st.markdown("---")
    st.caption("AI: Llama 3.3 Active")

# --- MAIN CONTENT ---
if mode == "💬 Chat Terminal":
    st.markdown("<div class='header-logo'>⚡ <span>NEXUS</span> GOLD</div>", unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_box = st.container()
    with chat_box:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"<div class='chat-container user-msg'><div class='bubble bubble-user'>{msg['content']}</div></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='chat-container'><div class='avatar-ai'>🤖</div><div class='bubble bubble-ai'>{msg['content']}</div></div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Message NEXUS..."):
        st.session_state.messages.append({"role": "user", "content": prompt}); st.rerun()

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
            st.session_state.messages.append({"role": "assistant", "content": f_res}); st.rerun()

elif mode == "📈 Assets Dashboard":
    st.markdown("### 📈 Inventory Assets Dashboard")
    stats = get_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-val'>{stats['total']}</div><div class='metric-label'>Total Assets</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='metric-val'>{stats['active']}</div><div class='metric-label'>Active Stock</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div class='metric-val' style='color:#f87171;'>{stats['low']}</div><div class='metric-label'>Low Inventory</div></div>", unsafe_allow_html=True)
    
    st.markdown("<br>#### 📂 Recent Asset Activity", unsafe_allow_html=True)
    data = query_db("SELECT * FROM Assets LIMIT 10")
    if "data" in data:
        st.dataframe(pd.DataFrame(data['data'], columns=data['cols']), use_container_width=True)

elif mode == "🏗️ System Architecture":
    st.markdown("### 🏗️ Knowledge Graph Agent Architecture")
    st.mermaid("""
    graph TD
        User((User Request)) --> UI[Streamlit UI]
        UI --> Classifier{Intent Detection}
        
        Classifier -- "Data Request" --> Gen[Llama 3.3 SQL Generator]
        Gen --> Executor[SQLite Engine]
        Executor --> Summary[Llama 3.3 Summarizer]
        
        Classifier -- "Conversational" --> Direct[Llama 3.3 Chat]
        
        Summary --> Response[AI Response]
        Direct --> Response
        
        subgraph Memory Engine
            History[(35 Turn Buffer)]
        end
        History -.-> Classifier
        History -.-> Gen
    """)

else:
    st.markdown("### ✨ Key Features")
    st.info("NEXUS is optimized for high-performance inventory management.")
