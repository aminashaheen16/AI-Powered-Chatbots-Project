import streamlit as st
import sys
import os
import time

# Ensure path is correct
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from inventory_bot.state_machine import inventory_app
    from knowledge_bot.agent import KnowledgeAgent
    from inventory_bot.database import execute_query
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

# --- Page Config ---
st.set_page_config(page_title="NEXUS", page_icon="💡", layout="wide")

# --- Ultra-Minimalist CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .stApp { background-color: #ffffff; }
    
    /* Sidebar - Very Clean */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    /* NEXUS Header */
    .nexus-header {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -2px;
        color: #0f172a;
        margin-bottom: 5px;
    }
    
    .nexus-subtitle {
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 40px;
    }
    
    /* Chat Bubbles - Elegant & Minimal */
    .message-row { display: flex; margin-bottom: 20px; }
    .user-row { justify-content: flex-end; }
    .assistant-row { justify-content: flex-start; }
    
    .bubble {
        max-width: 75%;
        padding: 12px 18px;
        border-radius: 18px;
        font-size: 15px;
        line-height: 1.5;
    }
    
    .user-bubble {
        background-color: #0f172a;
        color: white;
        border-bottom-right-radius: 2px;
    }
    
    .assistant-bubble {
        background-color: #f1f5f9;
        color: #334155;
        border-bottom-left-radius: 2px;
    }
    
    /* Stats Widget */
    .stats-box {
        background: white;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    
    /* Hide Streamlit elements for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar Logic ---
def get_stats():
    try:
        res = execute_query("SELECT COUNT(*) FROM Assets WHERE status = 'Active'")
        return res['data'][0][0]
    except: return "0"

with st.sidebar:
    st.markdown("<div class='nexus-header'>NEXUS</div>", unsafe_allow_html=True)
    st.markdown("<div class='nexus-subtitle'>Enterprise Intelligence</div>", unsafe_allow_html=True)
    st.markdown("---")
    bot_type = st.selectbox("Engine", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"])
    st.markdown("---")
    st.markdown(f"<div class='stats-box'><small style='color:#64748b'>ACTIVE ASSETS</small><br><b>{get_stats()} Items</b></div>", unsafe_allow_html=True)
    st.caption("🟢 Core: Stable")

# --- Main Chat Area ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_bot" not in st.session_state or st.session_state.last_bot != bot_type:
    st.session_state.messages = []
    st.session_state.last_bot = bot_type

# Render Messages
for message in st.session_state.messages:
    role_class = "user-row" if message["role"] == "user" else "assistant-row"
    bubble_class = "user-bubble" if message["role"] == "user" else "assistant-bubble"
    st.markdown(f"<div class='message-row {role_class}'><div class='bubble {bubble_class}'>{message['content']}</div></div>", unsafe_allow_html=True)

# Input
if prompt := st.chat_input("Message NEXUS..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Processing Logic
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_prompt = st.session_state.messages[-1]["content"]
    with st.spinner(" "):
        max_retries = 3
        response = ""
        for i in range(max_retries):
            try:
                if bot_type == "Inventory Bot (SQL)":
                    result = inventory_app.invoke({
                        "user_input": last_prompt, "intent": "", "sql_query": "",
                        "query_results": None, "error": "", "history": [],
                        "response": "", "retry_count": 0
                    })
                    response = result["response"]
                else:
                    agent = KnowledgeAgent()
                    response = agent.handle_message(last_prompt)
                break
            except Exception as e:
                if "429" in str(e) and i < max_retries - 1:
                    time.sleep((i+1)*5)
                    continue
                else:
                    response = "System is currently busy. Please retry in 30 seconds."
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
