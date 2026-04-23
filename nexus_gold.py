import streamlit as st
import os
import sqlite3
import json
import time
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from streamlit_agraph import agraph, Node, Edge, Config

# --- CONFIG & LOAD ---
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- DB HELPERS ---
def query_db(sql):
    try:
        conn = sqlite3.connect('data/inventory.db')
        cursor = conn.cursor()
        cursor.execute(sql)
        res = cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        conn.close()
        return {"data": res, "cols": cols}
    except Exception as e:
        return {"error": str(e)}

# --- AI CORE WITH GRAPH EXTRACTION ---
def nex_ai_core(user_input, history):
    # 1. Intent & Graph Extraction
    extract_prompt = f"""
    Analyze: '{user_input}'.
    1. Categorize: ADD/INQUIRE/EDIT/DELETE/CHAT.
    2. Needs SQL? true/false.
    3. Extract Graph Entities: Respond in JSON only.
    Format: {{"intent": "...", "needs_sql": bool, "new_nodes": [{{ "id": "...", "label": "...", "type": "Person/Company/Project" }}], "new_edges": [{{ "source": "...", "target": "...", "label": "..." }}]}}
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a JSON extractor."}, {"role": "user", "content": extract_prompt}],
        response_format={"type": "json_object"}
    )
    data = json.loads(response.choices[0].message.content)
    
    # 2. SQL Logic (if needed)
    sql_context = ""
    if data.get("needs_sql"):
        sql_p = f"Generate SQL for: '{user_input}'. Table: Assets (name, quantity, status)."
        sql_res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Output ONLY SQL."}, {"role": "user", "content": sql_p}]
        ).choices[0].message.content.strip()
        db_res = query_db(sql_res.replace("```sql", "").replace("```", "").strip())
        sql_context = f" Database Results: {db_res}"
        
    # 3. Final Response
    messages = [{"role": "system", "content": "You are NEXUS, a Knowledge Graph Agent. Use context to answer."}]
    messages.extend(history[-20:])
    messages.append({"role": "user", "content": user_input + sql_context})
    
    stream = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages, stream=True)
    return stream, data

# --- UI SETUP ---
st.set_page_config(page_title="NEXUS KNOWLEDGE AGENT", page_icon="🔱", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #010409; color: #ffffff !important; }
    .chat-bubble-user { background: #7e22ce; padding: 12px 18px; border-radius: 20px 20px 0 20px; margin-bottom: 15px; margin-left: auto; max-width: 85%; }
    .chat-bubble-ai { background: #161b22; padding: 12px 18px; border-radius: 20px 20px 20px 0; margin-bottom: 15px; max-width: 85%; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE FOR GRAPH ---
if "nodes" not in st.session_state:
    st.session_state.nodes = [Node(id="Nexus", label="NEXUS AI", color="#c084fc", size=30)]
if "edges" not in st.session_state:
    st.session_state.edges = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#c084fc; font-weight:800;'>NEXUS AGENT</h2>", unsafe_allow_html=True)
    mode = st.radio("Navigation", ["💬 Chat & Graph", "✨ Features", "🏗️ Architecture"])
    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.nodes = [Node(id="Nexus", label="NEXUS AI", color="#c084fc", size=30)]
        st.session_state.edges = []
        st.rerun()

# --- MAIN LAYOUT ---
if mode == "💬 Chat & Graph":
    c_left, c_right = st.columns([1.1, 0.9])
    
    with c_right:
        st.markdown("#### 🕸️ Dynamic Knowledge Universe")
        config = Config(width=600, height=500, directed=True, nodeHighlightBehavior=True, highlightColor="#c084fc", backgroundColor="#010409")
        agraph(nodes=st.session_state.nodes, edges=st.session_state.edges, config=config)

    with c_left:
        st.markdown("#### 💬 Agent Terminal")
        chat_box = st.container(height=500)
        with chat_box:
            for msg in st.session_state.messages:
                cls = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-ai"
                st.markdown(f"<div class={cls}>{msg['content']}</div>", unsafe_allow_html=True)

        if prompt := st.chat_input("Ask or Tell NEXUS anything..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.markdown(f"<div class='chat-bubble-user'>{prompt}</div>", unsafe_allow_html=True)
            
            with chat_box:
                stream, metadata = nex_ai_core(prompt, st.session_state.messages[:-1])
                
                # Update Graph Nodes
                for n in metadata.get('new_nodes', []):
                    if not any(node.id == n['id'] for node in st.session_state.nodes):
                        st.session_state.nodes.append(Node(id=n['id'], label=n['label'], color="#818cf8", size=25))
                # Update Graph Edges
                for e in metadata.get('new_edges', []):
                    st.session_state.edges.append(Edge(source=e['source'], target=e['target'], label=e['label'], color="#30363d"))
                
                full_res = ""; res_box = st.empty()
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_res += chunk.choices[0].delta.content
                        res_box.markdown(f"<div class='chat-bubble-ai'>{full_res}▌</div>", unsafe_allow_html=True)
                res_box.markdown(f"<div class='chat-bubble-ai'>{full_res}</div>", unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                st.rerun()

elif mode == "✨ Features":
    st.markdown("### ✨ Key Features")
    st.info("Dynamic Intent Detection & Entity Extraction active.")

else:
    st.markdown("### 🏗️ System Architecture")
    st.mermaid("graph TD; User-->NEXUS; NEXUS-->Database; NEXUS-->KnowledgeGraph")
