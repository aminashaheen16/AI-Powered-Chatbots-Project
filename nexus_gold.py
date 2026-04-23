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

def get_stats():
    res = query_db("SELECT COUNT(*) FROM Assets")
    total = res['data'][0][0] if not res.get('error') else 0
    return total

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
        messages = [{"role": "system", "content": "You are NEXUS, a world-class inventory expert. Be concise and professional."}, {"role": "user", "content": final_prompt}]
    else:
        messages = [{"role": "system", "content": "You are NEXUS, a friendly and intelligent AI assistant. Respond with personality."}, {"role": "user", "content": user_input}]

    # Return stream for better UX
    return client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=True
    )

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS GOLD PRO", page_icon="🔱", layout="wide")

# Custom CSS for Premium Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    
    .stApp { background: radial-gradient(circle at top right, #1e1b4b, #020617); color: #ffffff !important; }
    
    [data-testid="stSidebar"] { background-color: rgba(2, 6, 23, 0.8) !important; backdrop-filter: blur(10px); border-right: 1px solid rgba(255,255,255,0.05); }
    
    .stat-card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 15px; text-align: center; }
    .stat-value { font-size: 1.8rem; font-weight: 800; color: #c084fc; }
    .stat-label { font-size: 0.8rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }
    
    .chat-bubble-user { background: linear-gradient(135deg, #7e22ce, #9333ea); padding: 15px 20px; border-radius: 20px 20px 0 20px; margin-bottom: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.2); max-width: 80%; margin-left: auto; }
    .chat-bubble-ai { background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255,255,255,0.1); padding: 15px 20px; border-radius: 20px 20px 20px 0; margin-bottom: 15px; backdrop-filter: blur(5px); max-width: 80%; }
    
    .stChatInputContainer { border-radius: 30px !important; border: 1px solid rgba(255,255,255,0.1) !important; background: rgba(15, 23, 42, 0.8) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='background: linear-gradient(45deg, #c084fc, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;'>NEXUS GOLD</h1>", unsafe_allow_html=True)
    st.caption("v2.0 | Enterprise Edition")
    st.markdown("---")
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.info("System optimized for Groq Llama 3.3. Database connected and secured.")

# --- TOP STATS ---
total_assets = get_stats()
s1, s2, s3, s4 = st.columns(4)
with s1: st.markdown(f"<div class='stat-card'><div class='stat-label'>Total Assets</div><div class='stat-value'>{total_assets}</div></div>", unsafe_allow_html=True)
with s2: st.markdown("<div class='stat-card'><div class='stat-label'>System Status</div><div class='stat-value' style='color:#4ade80'>Stable</div></div>", unsafe_allow_html=True)
with s3: st.markdown("<div class='stat-card'><div class='stat-label'>AI Engine</div><div class='stat-value' style='color:#818cf8'>Llama 3.3</div></div>", unsafe_allow_html=True)
with s4: st.markdown("<div class='stat-card'><div class='stat-label'>Location</div><div class='stat-value' style='color:#f472b6'>Headquarters</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display history with custom bubbles
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bubble-ai'>{msg['content']}</div>", unsafe_allow_html=True)

if prompt := st.chat_input("Command NEXUS..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<div class='chat-bubble-user'>{prompt}</div>", unsafe_allow_html=True)

    with st.spinner(" "):
        full_response = ""
        stream = nex_ai_core(prompt)
        # Create a container for the streaming response
        res_box = st.empty()
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                res_box.markdown(f"<div class='chat-bubble-ai'>{full_response}▌</div>", unsafe_allow_html=True)
        
        res_box.markdown(f"<div class='chat-bubble-ai'>{full_response}</div>", unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
