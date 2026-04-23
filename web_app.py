import streamlit as st
import sys
import os
import time
import json
import uuid
import pandas as pd

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from inventory_bot.state_machine import inventory_app
    from knowledge_bot.agent import KnowledgeAgent
    from inventory_bot.database import execute_query
    from shared.llm_client import LLMClient
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

# --- Page Config ---
st.set_page_config(page_title="NEXUS AI", page_icon="🤖", layout="wide")

# --- Refined Deep Purple Theme CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    
    .stApp { 
        background: linear-gradient(135deg, #020617 0%, #0f172a 50%, #1e1b4b 100%) !important;
        background-attachment: fixed !important;
        color: #ffffff !important; 
    }
    
    [data-testid="stSidebar"] {
        background-color: rgba(2, 6, 23, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    .brand { font-size: 2.5rem; font-weight: 800; background: linear-gradient(45deg, #c084fc, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 30px; text-align: center; }
    
    .bubble { padding: 15px 20px; border-radius: 20px; font-size: 15px; line-height: 1.5; max-width: 70%; box-shadow: 0 4px 15px rgba(0,0,0,0.4); }
    .user-bubble { background-color: #7e22ce; color: #ffffff; border-bottom-right-radius: 5px; }
    .assistant-bubble { background-color: #1e293b; color: #e2e8f0; border: 1px solid rgba(255,255,255,0.1); border-bottom-left-radius: 5px; }
    
    .card { background-color: rgba(30, 41, 59, 0.5); padding: 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05); text-align: center; transition: 0.3s; }
    .card:hover { border-color: #a855f7; background-color: rgba(30, 41, 59, 0.8); }
    
    .stChatInputContainer { border-radius: 30px !important; background-color: #1e293b !important; border: 1px solid rgba(255,255,255,0.1) !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Session Management ---
HISTORY_FILE = os.path.join(current_dir, "data/sessions.json")
if "sessions" not in st.session_state:
    st.session_state.sessions = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                content = f.read()
                if content: st.session_state.sessions = json.loads(content)
        except: pass

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.sessions[st.session_state.current_session_id] = {"title": "New Session", "messages": [], "bot_type": "Inventory Bot (SQL)"}

# --- Sidebar ---
with st.sidebar:
    st.markdown("<div class='brand'>NEXUS AI</div>", unsafe_allow_html=True)
    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.sessions[st.session_state.current_session_id] = {"title": "New Session", "messages": [], "bot_type": "Inventory Bot (SQL)"}
        st.rerun()
    st.markdown("---")
    for sid, data in list(st.session_state.sessions.items())[::-1][:8]:
        if st.button(data["title"], key=sid, use_container_width=True):
            st.session_state.current_session_id = sid
            st.rerun()

# --- Main App ---
st.markdown("<div style='display:flex; justify-content:space-between;'><h3>Insights Dashboard</h3><p>🟢 Active Engine</p></div>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1: st.markdown("<div class='card'>📦<br><b>Inventory</b></div>", unsafe_allow_html=True)
with col2: st.markdown("<div class='card'>🕸️<br><b>Knowledge</b></div>", unsafe_allow_html=True)
with col3: st.markdown("<div class='card'>📊<br><b>Analytics</b></div>", unsafe_allow_html=True)
with col4: st.markdown("<div class='card'>⚙️<br><b>Settings</b></div>", unsafe_allow_html=True)
st.markdown("---")

current_session = st.session_state.sessions[st.session_state.current_session_id]
bot_type = st.selectbox("Protocol", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"])
current_session["bot_type"] = bot_type

for msg in current_session["messages"]:
    align = "justify-content: flex-end" if msg["role"] == "user" else "justify-content: flex-start"
    bubble = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
    st.markdown(f"<div style='display:flex; {align}; margin-bottom:20px;'><div class='bubble {bubble}'>{msg['content']}</div></div>", unsafe_allow_html=True)

if prompt := st.chat_input("Enter message..."):
    if current_session["title"] == "New Session": current_session["title"] = prompt[:25]
    current_session["messages"].append({"role": "user", "content": prompt})
    st.rerun()

if current_session["messages"] and current_session["messages"][-1]["role"] == "user":
    with st.spinner(" "):
        try:
            llm = LLMClient()
            if bot_type == "Inventory Bot (SQL)":
                result = inventory_app.invoke({"user_input": prompt, "intent": "", "sql_query": "", "query_results": None, "error": "", "history": [], "response": "", "retry_count": 0})
                response = result["response"]
            else:
                agent = KnowledgeAgent(); response = agent.handle_message(prompt)
            
            full_res = ""
            ph = st.empty()
            for chunk in response.split(" "):
                full_res += chunk + " "
                ph.markdown(f"<div style='display:flex; justify-content:flex-start; margin-bottom:20px;'><div class='bubble assistant-bubble'>{full_res}▌</div></div>", unsafe_allow_html=True)
                time.sleep(0.04)
            ph.markdown(f"<div style='display:flex; justify-content:flex-start; margin-bottom:20px;'><div class='bubble assistant-bubble'>{full_res}</div></div>", unsafe_allow_html=True)
            
            current_session["messages"].append({"role": "assistant", "content": full_res})
            with open(HISTORY_FILE, "w") as f: json.dump(st.session_state.sessions, f, indent=4)
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")
