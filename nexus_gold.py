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
    # Determine if SQL is needed
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
        messages = [{"role": "system", "content": "You are NEXUS, an expert AI."}]
        messages.extend(history[-25:])
        messages.append({"role": "user", "content": final_prompt})
    else:
        messages = [{"role": "system", "content": "You are NEXUS, a friendly AI assistant with deep memory."}]
        messages.extend(history[-35:])
        messages.append({"role": "user", "content": user_input})

    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS GOLD", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #010409 !important; color: #ffffff !important; }
    
    /* Logo styling */
    .header-logo { font-size: 2.2rem; font-weight: 800; color: #ffffff; padding: 20px 0; text-align: left; margin-bottom: 30px; }
    .header-logo span { color: #c084fc; }
    
    /* Chat Bubble Styling */
    .chat-container { display: flex; align-items: flex-start; margin-bottom: 25px; width: 100%; }
    .user-msg { justify-content: flex-end; }
    
    .bubble { padding: 15px 22px; border-radius: 20px; max-width: 85%; line-height: 1.6; font-size: 1.05rem; }
    .bubble-user { background: #7e22ce; color: white; border-radius: 22px 22px 0 22px; margin-left: auto; box-shadow: 0 4px 15px rgba(126, 34, 206, 0.2); }
    .bubble-ai { background: #1e293b; color: #f1f5f9; border: 1px solid rgba(255,255,255,0.05); border-radius: 22px 22px 22px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    
    .avatar-ai { width: 40px; height: 40px; background: #fbbf24; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-size: 1.3rem; flex-shrink: 0; }
    
    /* ChatGPT-like Input Bar */
    .stChatInputContainer { background-color: #010409 !important; border: 1px solid #30363d !important; border-radius: 15px !important; }
    .stChatInputContainer textarea { color: white !important; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background: #010409 !important; border-right: 1px solid #1e293b; }
    .stButton > button { background-color: #7e22ce !important; color: white !important; border-radius: 12px !important; border: none !important; font-weight: 600 !important; height: 48px !important; }
    
    header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#c084fc; font-weight:800; margin-top:20px;'>NEXUS GOLD</h2>", unsafe_allow_html=True)
    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.messages = []; st.rerun()
    st.markdown("---")
    st.caption("v2.5 | Enterprise Chat")
    st.caption("AI: Llama 3.3 Active")

# --- HEADER ---
st.markdown("<div class='header-logo'>⚡ <span>NEXUS</span> GOLD</div>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display messages
chat_box = st.container()
with chat_box:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-container user-msg'><div class='bubble bubble-user'>{msg['content']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-container'><div class='avatar-ai'>🤖</div><div class='bubble bubble-ai'>{msg['content']}</div></div>", unsafe_allow_html=True)

if prompt := st.chat_input("Ask NEXUS anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# AI Response Logic
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
