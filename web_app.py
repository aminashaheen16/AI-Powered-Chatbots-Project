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
st.set_page_config(page_title="Nexus AI | Chatbot Suite", page_icon="⚡", layout="wide")

# --- Custom CSS for Premium Look ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #020617 !important;
        border-right: 1px solid #334155;
    }
    
    /* Chat message styling */
    .stChatMessage {
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #334155;
    }
    
    /* User message */
    div[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #1e293b;
    }
    
    /* Assistant message */
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #0f172a;
        border-left: 5px solid #3b82f6;
    }
    
    /* Titles and Headers */
    h1 {
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        letter-spacing: -1px;
        background: -webkit-linear-gradient(#3b82f6, #2dd4bf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Input Box */
    .stChatInputContainer {
        border-radius: 20px;
        border: 1px solid #3b82f6;
    }
    
    /* Sidebar text */
    .css-17l2qt2 {
        color: #94a3b8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2040/2040504.png", width=80)
    st.title("Nexus AI")
    st.markdown("---")
    bot_type = st.selectbox("Select Active Engine", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"])
    st.markdown("---")
    st.info("⚡ **System Status**: Online")
    st.caption("Powered by Gemini 1.5 Flash")

# --- Main App ---
st.title("⚡ Nexus AI Chatbot Suite")
st.subheader(f"Interface: {bot_type}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Clear history when switching bots
if "last_bot" not in st.session_state or st.session_state.last_bot != bot_type:
    st.session_state.messages = []
    st.session_state.last_bot = bot_type

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Enter your query here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Processing through AI Engine..."):
            try:
                if bot_type == "Inventory Bot (SQL)":
                    result = inventory_app.invoke({
                        "user_input": prompt,
                        "intent": "",
                        "sql_query": "",
                        "query_results": None,
                        "error": "",
                        "history": [],
                        "response": "",
                        "retry_count": 0
                    })
                    response = result["response"]
                else:
                    agent = KnowledgeAgent()
                    response = agent.handle_message(prompt)
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Engine Error: {e}")

# Footer
st.markdown("---")
st.caption("© 2026 AI-Powered Chatbots Project | Advanced Agentic Coding")
