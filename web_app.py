import streamlit as st
import sys
import os

# Ensure the root directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from inventory_bot.state_machine import inventory_app
    from knowledge_bot.agent import KnowledgeAgent
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

# --- Page Config ---
st.set_page_config(page_title="Nexus AI | Futuristic Suite", page_icon="💎", layout="wide")

# --- Glassmorphism CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background: url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-1.2.1&auto=format&fit=crop&w=1950&q=80');
        background-size: cover;
        background-attachment: fixed;
    }

    .stApp {
        background: rgba(15, 23, 42, 0.7); /* Overlay to make text readable */
    }

    /* Glassmorphism containers */
    div[data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        margin: 15px 0 !important;
    }

    /* Sidebar Glassmorphism */
    section[data-testid="stSidebar"] {
        background: rgba(2, 6, 23, 0.8) !important;
        backdrop-filter: blur(15px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Titles */
    h1 {
        font-size: 3rem !important;
        font-weight: 800 !important;
        background: linear-gradient(to right, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0px 10px 20px rgba(0,0,0,0.2);
    }

    /* Chat Input */
    .stChatInputContainer {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 30px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* Buttons and Selectbox */
    .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 10px !important;
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stChatMessage {
        animation: fadeIn 0.5s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("<div style='text-align: center;'><img src='https://cdn-icons-png.flaticon.com/512/2040/2040504.png' width='100'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 2rem !important;'>NEXUS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Quantum Chat Engine v3.0</p>", unsafe_allow_html=True)
    st.markdown("---")
    bot_type = st.selectbox("Switch Core Engine", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"])
    st.markdown("---")
    st.markdown("🟢 **Engine Status**: Optimized")
    st.markdown("🧠 **Memory**: Active (Long-Term)")

# --- Main App ---
st.title("💎 Nexus AI Suite")
st.markdown(f"**Current Protocol:** {bot_type}")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_bot" not in st.session_state or st.session_state.last_bot != bot_type:
    st.session_state.messages = []
    st.session_state.last_bot = bot_type

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Initiate query..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing data through quantum neural nodes..."):
            try:
                if bot_type == "Inventory Bot (SQL)":
                    result = inventory_app.invoke({
                        "user_input": prompt, "intent": "", "sql_query": "",
                        "query_results": None, "error": "", "history": [],
                        "response": "", "retry_count": 0
                    })
                    response = result["response"]
                else:
                    agent = KnowledgeAgent()
                    response = agent.handle_message(prompt)
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Execution Error: {e}")

st.markdown("---")
st.markdown("<p style='text-align: center; opacity: 0.5;'>NEXUS AI © 2026 | Next-Gen AI Interfaces</p>", unsafe_allow_html=True)
