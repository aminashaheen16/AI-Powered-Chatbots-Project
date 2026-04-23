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

# --- DB INITIALIZATION FOR AgriAI ---
def init_agri_db():
    conn = sqlite3.connect('data/agri_logic.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS AgriAssets 
                 (id INTEGER PRIMARY KEY, item TEXT, type TEXT, value TEXT, status TEXT)''')
    # Seed with project-specific data
    data = [
        (1, 'Soil Moisture Sensor v2', 'Sensor', '45%', 'Active'),
        (2, 'ESP32 Node-1', 'Controller', 'Online', 'Active'),
        (3, 'Water Pump Alpha', 'Actuator', 'Off', 'Standby'),
        (4, 'DHT11 Temp Sensor', 'Sensor', '28°C', 'Low Battery'),
        (5, 'NPK Sensor', 'Sensor', 'Optimal', 'Active')
    ]
    c.executemany("INSERT OR IGNORE INTO AgriAssets VALUES (?,?,?,?,?)", data)
    conn.commit()
    conn.close()

init_agri_db()

def query_agri_db(sql):
    try:
        conn = sqlite3.connect('data/agri_logic.db')
        cursor = conn.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        conn.close()
        return {"data": res, "cols": cols}
    except Exception as e:
        return {"error": str(e)}

def get_agri_stats():
    try:
        conn = sqlite3.connect('data/agri_logic.db')
        c = conn.cursor()
        total_nodes = c.execute("SELECT COUNT(*) FROM AgriAssets WHERE type='Sensor' OR type='Controller'").fetchone()[0]
        active_sensors = c.execute("SELECT COUNT(*) FROM AgriAssets WHERE status='Active'").fetchone()[0]
        alerts = c.execute("SELECT COUNT(*) FROM AgriAssets WHERE status='Low Battery'").fetchone()[0]
        conn.close()
        return {"total": total_nodes, "active": active_sensors, "alerts": alerts}
    except:
        return {"total": 0, "active": 0, "alerts": 0}

# --- AI CORE FOR AgriAI ---
def agri_ai_core(user_input, history):
    decision_prompt = f"Does this agri query need project data? User: '{user_input}'. Respond JSON: {{\"data_needed\": true/false}}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are an AgriAI classifier."}, {"role": "user", "content": decision_prompt}],
        response_format={"type": "json_object"}
    )
    decision = json.loads(response.choices[0].message.content)
    
    if decision.get("data_needed"):
        sql_p = f"Generate SQL for AgriAssets table (id, item, type, value, status) for: '{user_input}'. Respond ONLY SQL."
        sql_res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Output ONLY SQL."}, {"role": "user", "content": sql_p}]
        ).choices[0].message.content.strip()
        db_res = query_agri_db(sql_res.replace("```sql", "").replace("```", "").strip())
        final_prompt = f"As the Soil For Soul AI, explain these sensor/asset results: {db_res} for user: {user_input}"
        messages = [{"role": "system", "content": "You are the Soil For Soul AI (AgriAI). You are expert in ESP32, soil sensors, and farm automation."}]
        messages.extend(history[-25:])
        messages.append({"role": "user", "content": final_prompt})
    else:
        messages = [{"role": "system", "content": "You are the Soil For Soul AI (AgriAI). You help with agricultural automation and sensor data."}]
        messages.extend(history[-35:])
        messages.append({"role": "user", "content": user_input})

    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)

# --- UI SETUP ---
st.set_page_config(page_title="Soil For Soul | AgriAI", page_icon="🌱", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #020617 !important; color: #ffffff !important; }
    
    .header-logo { font-size: 2.2rem; font-weight: 800; color: #ffffff; padding: 20px 0; }
    .header-logo span { color: #10b981; }
    
    .metric-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 15px; padding: 25px; text-align: center; }
    .metric-val { font-size: 2.5rem; font-weight: 800; color: #10b981; }
    .metric-label { font-size: 0.9rem; color: #94a3b8; }
    
    .chat-bubble-user { background: #059669; color: white; padding: 15px 22px; border-radius: 20px 20px 0 20px; margin-bottom: 20px; margin-left: auto; width: fit-content; max-width: 80%; }
    .chat-bubble-ai { background: #1e293b; color: #f1f5f9; border: 1px solid rgba(255,255,255,0.05); padding: 15px 22px; border-radius: 20px 20px 20px 0; margin-bottom: 20px; width: fit-content; max-width: 80%; }
    
    [data-testid="stSidebar"] { background: #010409 !important; border-right: 1px solid #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#10b981; font-weight:800; margin-top:20px;'>AgriAI PRO</h2>", unsafe_allow_html=True)
    st.caption("Soil For Soul Intelligence")
    mode = st.radio("Navigation", ["💬 Agri Chat", "📊 Sensor Dashboard", "🏗️ Project Architecture", "✨ Tech Specs"])
    if st.button("＋ New Session", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- MAIN CONTENT ---
if mode == "💬 Agri Chat":
    st.markdown("<div class='header-logo'>🌱 <span>Soil For Soul</span> AI</div>", unsafe_allow_html=True)
    if "messages" not in st.session_state: st.session_state.messages = []
    
    chat_box = st.container()
    with chat_box:
        for msg in st.session_state.messages:
            cls = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-ai"
            st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Ask about your farm nodes or soil sensors..."):
        st.session_state.messages.append({"role": "user", "content": prompt}); st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_p = st.session_state.messages[-1]["content"]
        with chat_box:
            stream = agri_ai_core(last_p, st.session_state.messages[:-1])
            f_res = ""; r_box = st.empty()
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    f_res += chunk.choices[0].delta.content
                    r_box.markdown(f"<div class='chat-bubble-ai'>{f_res}▌</div>", unsafe_allow_html=True)
            r_box.markdown(f"<div class='chat-bubble-ai'>{f_res}</div>", unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": f_res}); st.rerun()

elif mode == "📊 Sensor Dashboard":
    st.markdown("### 📊 Soil For Soul | Live Sensor Dashboard")
    stats = get_agri_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-val'>{stats['total']}</div><div class='metric-label'>Total IoT Nodes</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='metric-val'>{stats['active']}</div><div class='metric-label'>Active Sensors</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div class='metric-val' style='color:#f87171;'>{stats['alerts']}</div><div class='metric-label'>System Alerts</div></div>", unsafe_allow_html=True)
    
    st.markdown("<br>#### 🛰️ Real-time Sensor Matrix", unsafe_allow_html=True)
    data = query_agri_db("SELECT * FROM AgriAssets")
    if "data" in data:
        st.dataframe(pd.DataFrame(data['data'], columns=data['cols']), use_container_width=True)

elif mode == "🏗️ Project Architecture":
    st.markdown("### 🏗️ Soil For Soul | System Architecture")
    st.mermaid("""
    graph TD
        Sensors[Soil Moisture / DHT11] --> ESP32[ESP32 Controller]
        ESP32 --> Cloud[Firebase / Cloud Storage]
        Cloud --> AI[NEXUS AgriAI Engine]
        AI --> UI[User Interface]
        UI --> Insights[Farming Insights]
    """)
