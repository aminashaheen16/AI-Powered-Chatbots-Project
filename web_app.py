import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from inventory_bot.state_machine import inventory_app
from knowledge_bot.agent import KnowledgeAgent

st.set_page_config(page_title="AI Chatbot Suite", page_icon="🤖", layout="wide")

st.title("🤖 AI-Powered Chatbot Suite")
st.markdown("---")

# Sidebar for bot selection
bot_type = st.sidebar.selectbox("Choose Chatbot", ["Inventory Bot (SQL)", "Knowledge Graph Bot (Neo4j)"])

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
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if bot_type == "Inventory Bot (SQL)":
                    # Call Inventory Bot
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
                    # Call Knowledge Bot
                    agent = KnowledgeAgent()
                    response = agent.handle_message(prompt)
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {e}")

st.sidebar.markdown("---")
st.sidebar.info(f"Current Bot: **{bot_type}**")
