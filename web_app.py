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

# --- Futuristic Purple Dark Theme CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    * { font-family: 'Outfit', sans-serif; }
    
    .stApp { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #1f1f1f !important;
    }
    
    /* NEXUS Branding */
    .brand {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(45deg, #a855f7, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 30px;
        text-align: center;
    }
    
    /* Chat Bubbles like the Image */
    .message-row { display: flex; margin-bottom: 20px; align-items: flex-start; }
    .user-row { justify-content: flex-end; }
    .assistant-row { justify-content: flex-start; }
    
    .bubble {
        padding: 15px 20px;
        border-radius: 20px;
        font-size: 15px;
        line-height: 1.5;
        max-width: 70%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .user-bubble {
        background-color: #9333ea;
        color: #ffffff;
        border-bottom-right-radius: 5px;
    }
    
    .assistant-bubble {
        background-color: #1a1a1a;
        color: #e5e7eb;
        border: 1px solid #333333;
        border-bottom-left-radius: 5px;
    }
    
    /* Explore Cards */
    .card {
        background-color: #121212;
        padding: 20px;
        border-radius: 20px;
        border: 1px solid #1f1f1f;
        text-align: center;
        transition: 0.3s;
    }
    .card:hover { border-color: #9333ea; transform: translateY(-5px); }
    .card-icon { font-size: 2rem; margin-bottom: 10px; }
    
    /* Custom Input */
    .stChatInputContainer {
        border-radius: 30px !important;
        background-color: #121212 !important;
        border: 1px solid #333333 !important;
    }
    
    /* Status Dots */
    .dot { height: 10px; width: 10px; background-color: #22c55e; border-radius: 50%; display: inline-block; margin-right: 5px; }
    
    /* Scrollbar */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #000; }
    ::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- Session & History ---
HISTORY_FILE = os.path.join(current_dir, "data/sessions.json")
if "sessions" not in st.session_state:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f: st.session_state.sessions = json.load(f)
    else: st.session_state.sessions = {}

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.sessions[st.session_state.current_session_id] = {"title": "New Session", "messages": [], "bot_type": "Inventory Bot (SQL)"}

# --- Sidebar ---
with st.sidebar:
    st.markdown("<div class='brand'>NEXUS AI</div>", unsafe_allow_html=True)
    if st.button("＋ New Conversation", use_container_width=True):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.sessions[st.session_state.current_session_id] = {"title": "New Session", "messages": [], "bot_type": "Inventory Bot (SQL)"}
        st.rerun()
    
    st.markdown("---")
    st.markdown("<p style='color:#666; font-size:0.8rem;'>RECENT CHATS</p>", unsafe_allow_html=True)
    for sid, data in list(st.session_state.sessions.items())[::-1][:10]:
        active_style = "border: 1px solid #9333ea;" if sid == st.session_state.current_session_id else ""
        if st.button(data["title"], key=sid, use_container_width=True):
            st.session_state.current_session_id = sid
            st.rerun()

# --- Main App ---
st.markdown("<div style='display:flex; justify-content:space-between; align-items:center;'><h3>Explore Engine</h3><p><span class='dot'></span>System Active</p></div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1: st.markdown("<div class='card'><div class='card-icon'>📦</div><b>Inventory</b><br><small>SQL Expert</small></div>", unsafe_allow_html=True)
with col2: st.markdown("<div class='card'><div class='card-icon'>🕸️</div><b>Knowledge</b><br><small>Neo4j Graph</small></div>", unsafe_allow_html=True)
with col3: st.markdown("<div class='card'><div class='card-icon'>📊</div><b>Analytics</b><br><small>Data Insights</small></div>", unsafe_allow_html=True)
with col4: st.markdown("<div class='card'><div class='card-icon'>⚙️</div><b>Settings</b><br><small>AI Tuning</small></div>", unsafe_allow_html=True)

st.markdown("---")

current_session = st.session_state.sessions[st.session_state.current_session_id]
bot_type = st.selectbox("Select Active Protocol", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"])
current_session["bot_type"] = bot_type

# Chat Display
chat_placeholder = st.container()
with chat_placeholder:
    for msg in current_session["messages"]:
        row_class = "user-row" if msg["role"] == "user" else "assistant-row"
        bubble_class = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
        st.markdown(f"<div class='message-row {row_class}'><div class='bubble {bubble_class}'>{msg['content']}</div></div>", unsafe_allow_html=True)

# Input
if prompt := st.chat_input("Ask anything..."):
    if current_session["title"] == "New Session": current_session["title"] = prompt[:25]
    current_session["messages"].append({"role": "user", "content": prompt})
    st.rerun()

# Response with Exponential Backoff
if current_session["messages"] and current_session["messages"][-1]["role"] == "user":
    with st.spinner(" "):
        try:
            llm = LLMClient()
            if bot_type == "Inventory Bot (SQL)":
                result = inventory_app.invoke({"user_input": prompt, "intent": "", "sql_query": "", "query_results": None, "error": "", "history": [], "response": "", "retry_count": 0})
                response = result["response"]
            else:
                agent = KnowledgeAgent(); response = agent.handle_message(prompt)
            
            # Simulated Streaming
            full_res = ""
            msg_placeholder = st.empty()
            for chunk in response.split(" "):
                full_res += chunk + " "
                msg_placeholder.markdown(f"<div class='message-row assistant-row'><div class='bubble assistant-bubble'>{full_res}▌</div></div>", unsafe_allow_html=True)
                time.sleep(0.04)
            msg_placeholder.markdown(f"<div class='message-row assistant-row'><div class='bubble assistant-bubble'>{full_res}</div></div>", unsafe_allow_html=True)
            
            current_session["messages"].append({"role": "assistant", "content": full_res})
            with open(HISTORY_FILE, "w") as f: json.dump(st.session_state.sessions, f, indent=4)
            st.rerun()
        except Exception as e:
            if "429" in str(e): st.toast("⏳ Service busy, retrying...", icon="⚠️")
            else: st.error(f"Error: {e}")
