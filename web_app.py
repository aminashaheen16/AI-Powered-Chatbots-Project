import streamlit as st
import sys
import os
import time
import json
import uuid

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

# --- Custom CSS (Ultra Minimalist) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #f8fafc !important; border-right: 1px solid #e2e8f0 !important; }
    .nexus-logo { font-size: 2rem; font-weight: 800; letter-spacing: -1.5px; color: #0f172a; margin-bottom: 20px; }
    .stButton button { width: 100%; border-radius: 8px; }
    .chat-history-item { 
        padding: 10px; border-radius: 8px; cursor: pointer; margin-bottom: 5px; font-size: 0.9rem;
        border: 1px solid transparent; transition: 0.2s;
    }
    .chat-history-item:hover { background-color: #f1f5f9; border-color: #e2e8f0; }
    .active-chat { background-color: #e2e8f0 !important; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- Session Management ---
HISTORY_FILE = os.path.join(current_dir, "data/sessions.json")
os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

if "sessions" not in st.session_state:
    st.session_state.sessions = load_history()

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.sessions[st.session_state.current_session_id] = {"title": "New Chat", "messages": [], "bot_type": "Inventory Bot (SQL)"}

# --- Sidebar ---
with st.sidebar:
    st.markdown("<div class='nexus-logo'>NEXUS</div>", unsafe_allow_html=True)
    
    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.sessions[st.session_state.current_session_id] = {"title": "New Chat", "messages": [], "bot_type": "Inventory Bot (SQL)"}
        st.rerun()
    
    st.markdown("---")
    st.markdown("<small style='color:#64748b'>HISTORY</small>", unsafe_allow_html=True)
    
    # List previous sessions
    for sid, data in list(st.session_state.sessions.items())[::-1]:
        active_class = "active-chat" if sid == st.session_state.current_session_id else ""
        if st.button(data["title"], key=sid, help=f"Switch to {data['title']}"):
            st.session_state.current_session_id = sid
            st.rerun()

    st.markdown("---")
    bot_type = st.selectbox("Engine", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"], 
                             index=0 if st.session_state.sessions[st.session_state.current_session_id]["bot_type"] == "Inventory Bot (SQL)" else 1)
    st.session_state.sessions[st.session_state.current_session_id]["bot_type"] = bot_type

# --- Main App ---
current_session = st.session_state.sessions[st.session_state.current_session_id]

# Display Messages
for message in current_session["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Message NEXUS..."):
    # Update Title if it's a new chat
    if current_session["title"] == "New Chat":
        current_session["title"] = prompt[:25] + ("..." if len(prompt) > 25 else "")
    
    current_session["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            llm = LLMClient()
            # For simplicity, we stream directly from LLM for chitchat/synthesis
            # In a real app, you'd wrap the graph logic for streaming, but here we'll simulate it for the final response
            
            if bot_type == "Inventory Bot (SQL)":
                # Get the final response from the graph
                result = inventory_app.invoke({
                    "user_input": prompt, "intent": "", "sql_query": "",
                    "query_results": None, "error": "", "history": [],
                    "response": "", "retry_count": 0
                })
                raw_response = result["response"]
            else:
                agent = KnowledgeAgent()
                raw_response = agent.handle_message(prompt)
            
            # Simulate streaming for the raw_response
            for chunk in raw_response.split(" "):
                full_response += chunk + " "
                response_placeholder.markdown(full_response + "▌")
                time.sleep(0.05)
            response_placeholder.markdown(full_response)
            
            current_session["messages"].append({"role": "assistant", "content": full_response})
            save_history(st.session_state.sessions)
            
        except Exception as e:
            st.error(f"Error: {e}")

st.sidebar.markdown("---")
st.sidebar.caption("🟢 Core: v4.0 (Streaming)")
