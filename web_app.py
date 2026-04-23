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

# --- Sidebar Theme Toggle ---
with st.sidebar:
    st.markdown("<h2 style='color: #38bdf8;'>NEXUS ERP</h2>", unsafe_allow_html=True)
    theme = st.radio("Appearance", ["Light Mode", "Dark Mode"], horizontal=True)
    st.markdown("---")

# --- Theme CSS Definition ---
if theme == "Dark Mode":
    bg_color = "#0f172a"
    sidebar_bg = "#020617"
    card_bg = "#1e293b"
    text_color = "#f8fafc"
    border_color = "#334155"
    bot_msg_bg = "#1e293b"
    header_bg = "#1e293b"
else:
    bg_color = "#f3f4f6"
    sidebar_bg = "#0f172a"
    card_bg = "#ffffff"
    text_color = "#1f2937"
    border_color = "#e5e7eb"
    bot_msg_bg = "#ffffff"
    header_bg = "#ffffff"

st.markdown(f"""
    <style>
    * {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
    .stApp {{ background-color: {bg_color} !important; color: {text_color} !important; }}
    
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; border-right: 1px solid {border_color} !important; }}
    
    .corp-header {{
        background-color: {header_bg};
        padding: 15px 30px;
        border-bottom: 2px solid {border_color};
        display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;
        color: {text_color};
    }}
    
    .metric-card {{
        background-color: {card_bg}; padding: 20px; border-radius: 10px;
        border: 1px solid {border_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        color: {text_color};
    }}
    
    .msg-box {{ padding: 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.6; }}
    .user-msg {{ background-color: #0369a1; border-left: 5px solid #38bdf8; color: #ffffff; }}
    .bot-msg {{ background-color: {bot_msg_bg}; border: 1px solid {border_color}; color: {text_color}; }}
    
    /* Tables and other elements */
    .stDataFrame {{ background-color: {card_bg} !important; }}
    h1, h2, h3, h4, p {{ color: {text_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- Logic: Data Fetching ---
def get_inventory_summary():
    res = execute_query("SELECT name, quantity, status FROM Assets")
    if "data" in res: return pd.DataFrame(res['data'], columns=res['columns'])
    return pd.DataFrame()

# --- History Management ---
HISTORY_FILE = os.path.join(current_dir, "data/sessions.json")
if "sessions" not in st.session_state:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f: st.session_state.sessions = json.load(f)
    else: st.session_state.sessions = {}

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.sessions[st.session_state.current_session_id] = {"title": "New Session", "messages": [], "bot_type": "Inventory Bot (SQL)"}

# --- Sidebar Navigation ---
with st.sidebar:
    if st.button("＋ New Ticket", use_container_width=True):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.sessions[st.session_state.current_session_id] = {"title": "New Session", "messages": [], "bot_type": "Inventory Bot (SQL)"}
        st.rerun()
    st.markdown("---")
    st.markdown("<small>RECENT SESSIONS</small>", unsafe_allow_html=True)
    for sid, data in list(st.session_state.sessions.items())[::-1][:10]:
        if st.button(data["title"], key=sid, use_container_width=True):
            st.session_state.current_session_id = sid
            st.rerun()

# --- Dashboard Header ---
st.markdown(f"""<div class='corp-header'><div><h3 style='margin:0;'>NEXUS Management Dashboard</h3><p style='margin:0; font-size:0.8rem; opacity:0.7;'>Enterprise Resource Intelligence</p></div></div>""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 Inventory Metrics", "💬 Support Assistant"])

with tab1:
    col1, col2, col3 = st.columns(3)
    df = get_inventory_summary()
    with col1: st.markdown(f"<div class='metric-card'><small>TOTAL ASSETS</small><h3>{df['quantity'].sum() if not df.empty else 0}</h3></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='metric-card'><small>ACTIVE UNITS</small><h3>{df[df['status']=='Active']['quantity'].sum() if not df.empty else 0}</h3></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='metric-card'><small>HEALTH STATUS</small><h3>Optimal</h3></div>", unsafe_allow_html=True)
    st.markdown("#### Inventory Ledger")
    if not df.empty: st.dataframe(df, use_container_width=True)
    else: st.info("No records found.")

with tab2:
    current_session = st.session_state.sessions[st.session_state.current_session_id]
    bot_type = st.selectbox("Select Intelligence Agent", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"])
    current_session["bot_type"] = bot_type
    
    for msg in current_session["messages"]:
        style = "user-msg" if msg["role"] == "user" else "bot-msg"
        st.markdown(f"<div class='msg-box {style}'><b>{msg['role'].upper()}:</b><br>{msg['content']}</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Input command..."):
        if current_session["title"] == "New Session": current_session["title"] = prompt[:30]
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
            except Exception as e: st.error(f"Error: {e}")
