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
st.set_page_config(page_title="NEXUS Enterprise", page_icon="🏢", layout="wide")

# --- Corporate CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');
    * { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    .stApp { background-color: #f3f4f6; }
    
    /* Sidebar - Corporate Navy */
    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }
    
    .sidebar-title { color: #38bdf8; font-size: 1.5rem; font-weight: 700; margin-bottom: 20px; }
    
    /* Corporate Header */
    .corp-header {
        background-color: #ffffff;
        padding: 15px 30px;
        border-bottom: 2px solid #e5e7eb;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    /* Stats Cards */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    /* Chat Bubbles - Clean Corporate */
    .msg-box { padding: 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.6; }
    .user-msg { background-color: #e0f2fe; border-left: 5px solid #0369a1; color: #0c4a6e; }
    .bot-msg { background-color: #ffffff; border: 1px solid #e5e7eb; color: #1f2937; }
    
    .stButton button { border-radius: 4px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- Logic: Data Fetching ---
def get_inventory_summary():
    res = execute_query("SELECT name, quantity, status FROM Assets")
    if "data" in res:
        return pd.DataFrame(res['data'], columns=res['columns'])
    return pd.DataFrame()

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
    st.markdown("<div class='sidebar-title'>NEXUS ERP</div>", unsafe_allow_html=True)
    if st.button("＋ New Support Ticket"):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.sessions[st.session_state.current_session_id] = {"title": "New Session", "messages": [], "bot_type": "Inventory Bot (SQL)"}
        st.rerun()
    
    st.markdown("---")
    st.markdown("<small>RECENT LOGS</small>", unsafe_allow_html=True)
    for sid, data in list(st.session_state.sessions.items())[::-1][:10]:
        if st.button(data["title"], key=sid):
            st.session_state.current_session_id = sid
            st.rerun()

# --- Main Dashboard ---
st.markdown("""<div class='corp-header'><div><h3 style='margin:0;'>Management Dashboard</h3><p style='margin:0; font-size:0.8rem; color:#6b7280;'>Enterprise Resource Intelligence</p></div></div>""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 Inventory Overview", "💬 AI Assistant"])

with tab1:
    col1, col2, col3 = st.columns(3)
    df = get_inventory_summary()
    with col1: st.markdown(f"<div class='metric-card'><small>TOTAL ASSETS</small><h3>{df['quantity'].sum() if not df.empty else 0}</h3></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='metric-card'><small>ACTIVE UNITS</small><h3>{df[df['status']=='Active']['quantity'].sum() if not df.empty else 0}</h3></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='metric-card'><small>CATEGORIES</small><h3>3</h3></div>", unsafe_allow_html=True)
    
    st.markdown("#### Detailed Inventory List")
    if not df.empty: st.dataframe(df, use_container_width=True)
    else: st.info("No assets found in the database.")

with tab2:
    current_session = st.session_state.sessions[st.session_state.current_session_id]
    bot_type = st.selectbox("Select AI Agent", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"])
    current_session["bot_type"] = bot_type
    
    chat_box = st.container()
    with chat_box:
        for msg in current_session["messages"]:
            style = "user-msg" if msg["role"] == "user" else "bot-msg"
            st.markdown(f"<div class='msg-box {style}'><b>{msg['role'].upper()}:</b><br>{msg['content']}</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Query the system..."):
        if current_session["title"] == "New Session":
            current_session["title"] = prompt[:30]
        
        current_session["messages"].append({"role": "user", "content": prompt})
        st.rerun()

    # Response Logic
    if current_session["messages"] and current_session["messages"][-1]["role"] == "user":
        with st.spinner("Analyzing corporate data..."):
            try:
                llm = LLMClient()
                if bot_type == "Inventory Bot (SQL)":
                    result = inventory_app.invoke({"user_input": prompt, "intent": "", "sql_query": "", "query_results": None, "error": "", "history": [], "response": "", "retry_count": 0})
                    response = result["response"]
                else:
                    agent = KnowledgeAgent(); response = agent.handle_message(prompt)
                
                # Streaming Simulation
                placeholder = st.empty()
                full_res = ""
                for chunk in response.split(" "):
                    full_res += chunk + " "
                    placeholder.markdown(f"<div class='msg-box bot-msg'><b>ASSISTANT:</b><br>{full_res}▌</div>", unsafe_allow_html=True)
                    time.sleep(0.04)
                placeholder.markdown(f"<div class='msg-box bot-msg'><b>ASSISTANT:</b><br>{full_res}</div>", unsafe_allow_html=True)
                
                current_session["messages"].append({"role": "assistant", "content": full_res})
                with open(HISTORY_FILE, "w") as f: json.dump(st.session_state.sessions, f, indent=4)
                st.rerun()
            except Exception as e: st.error(f"System Error: {e}")
