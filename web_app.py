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
st.set_page_config(page_title="NEXUS", page_icon="💡", layout="wide")

# --- Simple & Clean Gray Theme CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    * { font-family: 'Inter', sans-serif; }
    
    .stApp { background-color: #f3f4f6 !important; } /* Light Gray Background */
    
    /* Clean Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e5e7eb !important;
    }
    
    /* Elegant Content Cards */
    .content-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* Chat Bubbles - Simplified */
    .msg-row { display: flex; margin-bottom: 15px; }
    .bubble {
        padding: 12px 18px;
        border-radius: 12px;
        font-size: 15px;
        line-height: 1.5;
        max-width: 85%;
    }
    .user-bubble { background-color: #e5e7eb; color: #1f2937; }
    .bot-bubble { background-color: #ffffff; border: 1px solid #e5e7eb; color: #374151; }
    
    /* Professional Headers */
    h1, h2, h3 { color: #111827; font-weight: 700; }
    
    /* Discrete Loading/Error info */
    .status-msg { color: #6b7280; font-size: 0.85rem; font-style: italic; }
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
    st.session_state.sessions[st.session_state.current_session_id] = {"title": "New Chat", "messages": [], "bot_type": "Inventory Bot (SQL)"}

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2 style='color:#3b82f6'>NEXUS</h2>", unsafe_allow_html=True)
    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.sessions[st.session_state.current_session_id] = {"title": "New Chat", "messages": [], "bot_type": "Inventory Bot (SQL)"}
        st.rerun()
    st.markdown("---")
    st.markdown("<small style='color:#9ca3af'>HISTORY</small>", unsafe_allow_html=True)
    for sid, data in list(st.session_state.sessions.items())[::-1][:8]:
        if st.button(data["title"], key=sid, use_container_width=True):
            st.session_state.current_session_id = sid
            st.rerun()

# --- Main Interface ---
st.title("Nexus Intelligent Assistant")

tab1, tab2 = st.tabs(["💬 Chat", "📊 Inventory Stats"])

with tab2:
    try:
        res = execute_query("SELECT name, quantity, status FROM Assets")
        df = pd.DataFrame(res['data'], columns=res['columns'])
        st.markdown("<div class='content-card'>", unsafe_allow_html=True)
        st.markdown("### Asset Inventory")
        st.dataframe(df, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    except: st.info("Inventory table is loading...")

with tab1:
    current_session = st.session_state.sessions[st.session_state.current_session_id]
    bot_type = st.selectbox("Intelligence Mode", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"])
    current_session["bot_type"] = bot_type
    
    # Render messages in a clean list
    for msg in current_session["messages"]:
        align = "flex-end" if msg["role"] == "user" else "flex-start"
        bubble = "user-bubble" if msg["role"] == "user" else "bot-bubble"
        st.markdown(f"<div style='display:flex; justify-content:{align}; margin-bottom:10px;'><div class='bubble {bubble}'>{msg['content']}</div></div>", unsafe_allow_html=True)

    if prompt := st.chat_input("How can I help you?"):
        if current_session["title"] == "New Chat": current_session["title"] = prompt[:30]
        current_session["messages"].append({"role": "user", "content": prompt})
        st.rerun()

    # Response Logic with Silent Error Handling
    if current_session["messages"] and current_session["messages"][-1]["role"] == "user":
        placeholder = st.empty()
        with placeholder.container():
            st.markdown("<p class='status-msg'>AI is thinking...</p>", unsafe_allow_html=True)
            
            response = ""
            success = False
            for i in range(3):
                try:
                    if bot_type == "Inventory Bot (SQL)":
                        result = inventory_app.invoke({"user_input": prompt, "intent": "", "sql_query": "", "query_results": None, "error": "", "history": [], "response": "", "retry_count": 0})
                        response = result["response"]
                    else:
                        agent = KnowledgeAgent(); response = agent.handle_message(prompt)
                    success = True
                    break
                except Exception as e:
                    if "429" in str(e):
                        st.markdown(f"<p class='status-msg'>Service busy, retrying in { (i+1)*5 }s...</p>", unsafe_allow_html=True)
                        time.sleep((i+1)*5)
                    else:
                        response = "I encountered a technical issue. Please try again in a moment."
                        break
            
            if not success and not response:
                response = "The AI service is currently at capacity. Please wait 30 seconds."

            current_session["messages"].append({"role": "assistant", "content": response})
            with open(HISTORY_FILE, "w") as f: json.dump(st.session_state.sessions, f, indent=4)
            st.rerun()
