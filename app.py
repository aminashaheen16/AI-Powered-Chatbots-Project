import streamlit as st
import os
import time
import pandas as pd
from datetime import datetime
import inventory_bot as sql_bot
import knowledge_agent as neo_bot
import storage

# --- APP CONFIG ---
st.set_page_config(page_title="NEXUS PRO | Enterprise AI", page_icon="🔱", layout="wide")

# --- CUSTOM CSS (Premium Look) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    * { font-family: 'Outfit', sans-serif; }
    
    .stApp { background: #0b0e14; color: #e1e1e1; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #010409 !important;
        border-right: 1px solid #30363d;
    }
    
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: 800;
        color: #c084fc;
        margin-bottom: 20px;
    }
    
    /* Chat bubbles */
    .user-bubble {
        background: #7e22ce;
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 0px 18px;
        margin: 10px 0;
        max-width: 80%;
        margin-left: auto;
    }
    
    .ai-bubble {
        background: #161b22;
        border: 1px solid #30363d;
        color: #e6edf3;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 0px;
        margin: 10px 0;
        max-width: 80%;
    }
    
    .eval-badge {
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 10px;
        background: rgba(192, 132, 252, 0.1);
        color: #c084fc;
        border: 1px solid #c084fc;
        margin-top: 5px;
        display: inline-block;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        transition: 0.3s;
    }
    
    .stButton > button:hover {
        border-color: #7e22ce;
        color: #7e22ce;
    }
    
    .new-chat-btn > button {
        background-color: #7e22ce !important;
        color: white !important;
        font-weight: 600;
    }
    
    /* Session list */
    .session-item {
        padding: 8px 12px;
        border-radius: 8px;
        cursor: pointer;
        margin-bottom: 5px;
        transition: 0.2s;
        font-size: 0.9rem;
        color: #8b949e;
    }
    
    .session-item:hover {
        background: #21262d;
        color: #c084fc;
    }
    
    header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- INITIALIZE STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"
if "mode" not in st.session_state:
    st.session_state.mode = "SQL Inventory"

# --- SIDEBAR LOGIC ---
with st.sidebar:
    st.markdown("<div class='sidebar-header'>🔱 NEXUS PRO</div>", unsafe_allow_html=True)
    
    # Mode Selection
    st.session_state.mode = st.selectbox("Select Intelligence Core", ["SQL Inventory", "Neo4j Knowledge"])
    
    st.markdown("---")
    
    # New Chat Button
    if st.button("＋ New Chat", key="new_chat", help="Start a fresh conversation"):
        st.session_state.messages = []
        st.session_state.session_id = f"session_{int(time.time())}"
        st.rerun()
    
    st.markdown("---")
    
    # Chat History
    st.caption("RECENT SESSIONS")
    if st.session_state.mode == "SQL Inventory":
        sessions = storage.get_sql_sessions()
        for s in sessions[:8]:
            if st.button(f"📄 {s[:15]}...", key=f"btn_{s}"):
                st.session_state.session_id = s
                st.session_state.messages = [] # Logic to load from DB could be added
                st.rerun()
    else:
        sessions = storage.get_neo4j_sessions()
        for s in sessions[:8]:
            st.markdown(f"<div class='session-item'>🕸️ {s[:20]}</div>", unsafe_allow_html=True)
            
    st.markdown("---")
    
    # Delete Options
    if st.button("🗑️ Clear All History", key="clear_all"):
        if st.session_state.mode == "SQL Inventory":
            storage.delete_sql_history()
        else:
            storage.delete_neo4j_history()
        st.success("History wiped!")
        time.sleep(1)
        st.rerun()

# --- CHAT INTERFACE ---
st.markdown(f"### 🚀 {st.session_state.mode} Agent")
st.caption(f"Active Session: {st.session_state.session_id}")

# Display Chat Messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='user-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='ai-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
        if "eval" in msg:
            ev = msg["eval"]
            st.markdown(f"<div class='eval-badge'>Accuracy: {ev['accuracy_score']}/10 | {ev['feedback']}</div>", unsafe_allow_html=True)

# Chat Input
if prompt := st.chat_input("Enter your query here..."):
    # Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f"<div class='user-bubble'>{prompt}</div>", unsafe_allow_html=True)
    
    with st.spinner("NEXUS is thinking..."):
        try:
            if st.session_state.mode == "SQL Inventory":
                # SQL Bot Logic
                history = sql_bot.load_memory(st.session_state.session_id)
                sql = sql_bot.generator_node(prompt, history)
                results = sql_bot.executor_node(sql)
                
                if results["status"] == "error":
                    sql = sql_bot.corrector_node(sql, results["message"])
                    results = sql_bot.executor_node(sql)
                
                if results["status"] == "success":
                    answer = sql_bot.responder_node(prompt, results["data"])
                    eval_res = sql_bot.evaluation_node(prompt, sql, results["data"], answer)
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "eval": eval_res
                    })
                    sql_bot.save_memory(prompt, answer, st.session_state.session_id)
                else:
                    st.error(f"Execution Error: {results['message']}")
            
            else:
                # Neo4j Bot Logic
                agent = neo_bot.Neo4jAgent()
                history = agent.load_memory()
                cypher = neo_bot.cypher_generator_node(prompt, history)
                res = agent.execute_cypher(cypher)
                
                if res["status"] == "success":
                    # For demo synthesis
                    answer = f"The knowledge graph has been queried/updated. Result: {res['data']}"
                    eval_res = neo_bot.evaluation_node(prompt, cypher, res["data"], answer)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "eval": eval_res
                    })
                    agent.save_memory(prompt, answer)
                else:
                    st.error(f"Neo4j Error: {res['message']}")
                agent.close()
            
            st.rerun()
            
        except Exception as e:
            st.error(f"System Error: {e}")

# Footer
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center; color:#444; font-size:0.8rem;'>Powered by Groq Llama 3.3 | Developed for NEXUS PRO</div>", unsafe_allow_html=True)
