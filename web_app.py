import streamlit as st
import sys
import os
import time
import json

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
st.set_page_config(page_title="Nexus Pro | Enterprise AI", page_icon="🏦", layout="wide")

# --- Advanced Professional CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .stApp { background-color: #f9fafb; }
    
    /* Header Area */
    .main-header {
        background-color: #ffffff;
        padding: 20px;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 30px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Chat Container */
    .chat-container {
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* Custom Message Bubbles */
    .message-row { display: flex; margin-bottom: 25px; animation: fadeIn 0.3s ease-in-out; }
    .user-row { justify-content: flex-end; }
    .assistant-row { justify-content: flex-start; }
    
    .bubble {
        max-width: 80%;
        padding: 16px 20px;
        border-radius: 16px;
        line-height: 1.6;
        font-size: 15px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .user-bubble {
        background-color: #2563eb;
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    .assistant-bubble {
        background-color: white;
        color: #1f2937;
        border: 1px solid #e5e7eb;
        border-bottom-left-radius: 4px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111827 !important;
        color: white !important;
    }
    
    /* Dashboard Cards */
    .stat-card {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 15px;
        border: 1px solid #374151;
    }
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    """, unsafe_allow_html=True)

# --- Logic: Fetch Quick Stats ---
def get_stats():
    try:
        res = execute_query("SELECT COUNT(*) FROM Assets WHERE status = 'Active'")
        return res['data'][0][0]
    except: return "N/A"

# --- Sidebar Content ---
with st.sidebar:
    st.markdown("<h2 style='color: #60a5fa; margin-bottom: 0;'>NEXUS PRO</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9ca3af; font-size: 0.8rem;'>v3.4.0 • Enterprise Edition</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("<p style='color: #d1d5db; font-weight: 600;'>CONTROL PANEL</p>", unsafe_allow_html=True)
    bot_type = st.selectbox("Switch AI Engine", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"])
    
    st.markdown("---")
    st.markdown("<p style='color: #d1d5db; font-weight: 600;'>REAL-TIME STATS</p>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class='stat-card'>
            <p style='color: #9ca3af; margin-bottom: 0; font-size: 0.75rem;'>ACTIVE ASSETS</p>
            <p style='color: #fff; font-size: 1.5rem; font-weight: 700; margin-top: 0;'>{get_stats()}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.info("🟢 System: Optimal")
    st.caption("Authenticated as Amina")

# --- Main App Interface ---
st.markdown("""
    <div class='main-header'>
        <div>
            <h2 style='margin:0; color:#111827;'>AI Assistant</h2>
            <p style='margin:0; color:#6b7280; font-size:0.9rem;'>Engaged: """ + bot_type + """</p>
        </div>
        <div style='background-color:#eff6ff; color:#2563eb; padding:8px 16px; border-radius:20px; font-weight:600; font-size:0.8rem;'>
            Secure Session
        </div>
    </div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_bot" not in st.session_state or st.session_state.last_bot != bot_type:
    st.session_state.messages = []
    st.session_state.last_bot = bot_type

# Render Chat History
chat_placeholder = st.container()
with chat_placeholder:
    for message in st.session_state.messages:
        role_class = "user-row" if message["role"] == "user" else "assistant-row"
        bubble_class = "user-bubble" if message["role"] == "user" else "assistant-bubble"
        st.markdown(f"""
            <div class='message-row {role_class}'>
                <div class='bubble {bubble_class}'>{message["content"]}</div>
            </div>
        """, unsafe_allow_html=True)

# Input Bar (Fixed-like behavior)
if prompt := st.chat_input("Ask me a business question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Handle Response
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_prompt = st.session_state.messages[-1]["content"]
    with st.spinner("AI Engine generating response..."):
        time.sleep(1) # Visual comfort
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
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        except Exception as e:
            if "429" in str(e):
                st.warning("🔄 High volume detected. Retrying...")
                time.sleep(3)
                st.rerun()
            else:
                st.error(f"Engine Error: {e}")
