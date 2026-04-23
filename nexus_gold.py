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
    res = query_db("SELECT COUNT(*) FROM Assets")
    total = res['data'][0][0] if not res.get('error') else 0
    active = query_db("SELECT COUNT(*) FROM Assets WHERE status='Active'")['data'][0][0]
    return total, active

# --- AI CORE ---
def nex_ai_core(user_input):
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
        messages = [{"role": "system", "content": "You are NEXUS, a world-class inventory expert. Be concise."}, {"role": "user", "content": final_prompt}]
    else:
        messages = [{"role": "system", "content": "You are NEXUS, a friendly AI assistant."}, {"role": "user", "content": user_input}]

    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS PRO PLATFORM", page_icon="🔱", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #020617; color: #ffffff !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: rgba(255,255,255,0.02); border-radius: 10px; padding: 0 20px; color: #94a3b8; border: none; }
    .stTabs [aria-selected="true"] { background-color: rgba(126, 34, 206, 0.2); color: #c084fc; border-bottom: 2px solid #c084fc; }
    
    .stat-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); padding: 25px; border-radius: 20px; text-align: center; }
    .stat-value { font-size: 2.5rem; font-weight: 800; color: #c084fc; }
    
    .chat-bubble-user { background: #7e22ce; padding: 15px 20px; border-radius: 20px 20px 0 20px; margin-bottom: 15px; margin-left: auto; max-width: 70%; }
    .chat-bubble-ai { background: #1e293b; padding: 15px 20px; border-radius: 20px 20px 20px 0; margin-bottom: 15px; max-width: 70%; border: 1px solid rgba(255,255,255,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#c084fc; font-weight:800;'>NEXUS PRO</h1>", unsafe_allow_html=True)
    st.caption("Central Enterprise Platform")
    st.markdown("---")
    if st.button("🗑️ Reset All Sessions", use_container_width=True):
        st.session_state.messages = []; st.rerun()

# --- MAIN TABS ---
tab1, tab2 = st.tabs(["💬 AI Chat Terminal", "📊 Enterprise Dashboard"])

with tab1:
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        cls = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-ai"
        st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Ask NEXUS..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.markdown(f"<div class='chat-bubble-user'>{prompt}</div>", unsafe_allow_html=True)
        with st.chat_message("assistant", vertical_alignment="top"):
            full_res = ""; res_box = st.empty()
            for chunk in nex_ai_core(prompt):
                if chunk.choices[0].delta.content:
                    full_res += chunk.choices[0].delta.content
                    res_box.markdown(f"<div class='chat-bubble-ai'>{full_res}▌</div>", unsafe_allow_html=True)
            res_box.markdown(f"<div class='chat-bubble-ai'>{full_res}</div>", unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": full_res})

with tab2:
    st.markdown("### 📈 Asset Intelligence")
    total, active = get_stats()
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='stat-card'><div style='color:#94a3b8'>TOTAL ASSETS</div><div class='stat-value'>{total}</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='stat-card'><div style='color:#94a3b8'>ACTIVE ITEMS</div><div class='stat-value' style='color:#4ade80'>{active}</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='stat-card'><div style='color:#94a3b8'>AI UPTIME</div><div class='stat-value' style='color:#818cf8'>99.9%</div></div>", unsafe_allow_html=True)
    
    st.markdown("<br>#### 📋 Master Inventory List", unsafe_allow_html=True)
    db_data = query_db("SELECT * FROM Assets")
    if not db_data.get('error'):
        df = pd.DataFrame(db_data['data'], columns=db_data['cols'])
        st.dataframe(df, use_container_width=True, hide_index=True)
