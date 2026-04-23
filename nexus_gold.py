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
        messages = [{"role": "system", "content": "You are NEXUS, an inventory expert."}]
        messages.extend(history[-6:])
        messages.append({"role": "user", "content": final_prompt})
    else:
        messages = [{"role": "system", "content": "You are NEXUS, a friendly AI assistant."}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": user_input})

    return client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS GOLD", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #020617 !important; color: #ffffff !important; }
    
    /* Header styling - Left Aligned */
    .header-container { display: flex; align-items: center; justify-content: flex-start; padding: 10px 0; margin-bottom: 20px; }
    .header-logo { font-size: 2rem; font-weight: 800; color: #ffffff; }
    .header-logo span { color: #c084fc; }
    
    /* Chat bubbles */
    .chat-bubble-user { background: #7e22ce; color: #ffffff; padding: 12px 20px; border-radius: 20px 20px 0 20px; margin-bottom: 15px; margin-left: auto; width: fit-content; max-width: 80%; }
    .chat-bubble-ai { background: #1e293b; color: #f1f5f9; border: 1px solid rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 20px 20px 20px 0; margin-bottom: 15px; width: fit-content; max-width: 80%; line-height: 1.6; }
    
    /* Input Bar */
    .stChatInputContainer { background-color: #020617 !important; border: 1px solid #1e293b !important; border-radius: 20px !important; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] { background: #010409 !important; border-right: 1px solid #1e293b; }
    
    /* New Chat Button Styling */
    .stButton > button { background-color: #7e22ce !important; color: white !important; border-radius: 10px !important; border: none !important; font-weight: 600 !important; height: 45px !important; }
    .stButton > button:hover { background-color: #9333ea !important; box-shadow: 0 4px 15px rgba(126, 34, 206, 0.4) !important; }
    
    header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#c084fc; font-weight:800; margin-bottom:20px;'>NEXUS PRO</h2>", unsafe_allow_html=True)
    
    # NEW CHAT BUTTON
    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.caption("AI Status: Active")
    st.caption("DB Engine: Connected")

# --- HEADER ---
st.markdown("""
    <div class='header-container'>
        <div class='header-logo'>⚡ <span>NEXUS</span> GOLD</div>
    </div>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display messages
for msg in st.session_state.messages:
    cls = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-ai"
    st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)

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
