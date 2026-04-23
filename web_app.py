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
st.set_page_config(page_title="Nexus AI | Minimalist", page_icon="🏢", layout="wide")

# --- Minimalist CSS (Apple Style) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600&family=Inter:wght@400;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #f5f5f7 !important;
    }

    .stApp {
        background-color: #f5f5f7 !important;
    }

    /* Clean Chat Containers */
    div[data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e5e7 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02) !important;
        margin: 10px 0 !important;
        padding: 20px !important;
    }

    /* User Message Highlight */
    div[data-testid="stChatMessage"]:nth-child(even) {
        border-right: 4px solid #007aff !important;
    }

    /* Assistant Message Highlight */
    div[data-testid="stChatMessage"]:nth-child(odd) {
        border-left: 4px solid #34c759 !important;
    }

    /* Sidebar - Corporate Look */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e5e5e7 !important;
    }

    /* Professional Title */
    h1 {
        font-family: 'SF Pro Display', sans-serif;
        font-weight: 700 !important;
        color: #1d1d1f !important;
        letter-spacing: -0.5px;
    }

    /* Input Box - Clean */
    .stChatInputContainer {
        border-radius: 12px !important;
        border: 1px solid #d2d2d7 !important;
        background-color: #ffffff !important;
    }

    /* Custom scrollbar for a cleaner look */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f5f5f7;
    }
    ::-webkit-scrollbar-thumb {
        background: #d2d2d7;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2 style='color: #007aff;'>🏢 Nexus Enterprise</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.9rem; color: #86868b;'>Corporate Intelligence Suite</p>", unsafe_allow_html=True)
    st.markdown("---")
    bot_type = st.selectbox("Select Business Engine", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"])
    st.markdown("---")
    st.markdown("🟢 **System**: Operational")
    st.markdown("🔒 **Security**: End-to-End Encrypted")

# --- Main App ---
st.title("Nexus AI Assistant")
st.markdown(f"<p style='color: #86868b;'>Active Workflow: {bot_type}</p>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_bot" not in st.session_state or st.session_state.last_bot != bot_type:
    st.session_state.messages = []
    st.session_state.last_bot = bot_type

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Enter your business query..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing request..."):
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
                st.error(f"System Error: {e}")

st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #d2d2d7; font-size: 0.8rem;'>NEXUS ENTERPRISE © 2026</p>", unsafe_allow_html=True)
