import streamlit as st
import os
import time
import json
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import inventory_bot as sql_bot
import knowledge_agent as neo_bot
import storage
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="NEXUS PRO | Enterprise AI", page_icon="🔱", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    * { font-family: 'Outfit', sans-serif; }
    .stApp { background: #020617; color: #f8fafc; }
    [data-testid="stSidebar"] { background: rgba(15, 23, 42, 0.95) !important; backdrop-filter: blur(15px); border-right: 1px solid rgba(255, 255, 255, 0.1); }
    .nexus-header { font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #c084fc, #6366f1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 30px; }
    .premium-card { background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); padding: 35px; border-radius: 24px; transition: 0.4s; }
    .premium-card:hover { border-color: #c084fc; transform: translateY(-12px); background: rgba(30, 41, 59, 0.9); }
    .user-bubble { background: #6366f1; color: white; padding: 15px 20px; border-radius: 20px 20px 0 20px; margin: 10px 0; max-width: 85%; margin-left: auto; }
    .ai-bubble { background: #1e293b; border: 1px solid #334155; color: #f1f5f9; padding: 15px 20px; border-radius: 20px 20px 20px 0; margin: 10px 0; max-width: 85%; }
    .eval-badge { background: rgba(192, 132, 252, 0.15); border: 1px solid #c084fc; padding: 12px 20px; border-radius: 15px; color: #e9d5ff; font-size: 0.95rem; margin-top: 15px; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "session_id" not in st.session_state: st.session_id = f"s_{int(time.time())}"

with st.sidebar:
    st.markdown("<div style='font-size:2rem; font-weight:800; color:#c084fc;'>🔱 NEXUS PRO</div>", unsafe_allow_html=True)
    page = st.radio("SYSTEM NAVIGATION", ["💬 Chat Terminal", "📊 Analytics Dashboard", "🏗️ System Architecture", "✨ Core Innovations", "📜 Project Specs"])
    if page == "💬 Chat Terminal":
        st.session_state.mode = st.selectbox("Intelligence Core", ["SQL Inventory", "Neo4j Knowledge"])
        if st.button("＋ New Session"):
            st.session_state.messages = []
            st.rerun()

if page == "💬 Chat Terminal":
    st.markdown(f"<div class='nexus-header'>{st.session_state.mode}</div>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        role = "user-bubble" if msg["role"] == "user" else "ai-bubble"
        st.markdown(f"<div class='{role}'>{msg['content']}</div>", unsafe_allow_html=True)
        if msg.get("eval"):
            ev = msg["eval"]
            st.markdown(f"<div class='eval-badge'>⚖️ QA Audit: {ev['accuracy_score']}/10 — {ev['feedback']}</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_query = st.session_state.messages[-1]["content"]
        with st.spinner("Processing..."):
            try:
                if st.session_state.mode == "SQL Inventory":
                    # Unified Intent Check
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": "CHITCHAT or DB_QUERY? JSON: {'intent': '...'}"}, {"role": "user", "content": last_query}], response_format={"type": "json_object"}).choices[0].message.content
                    intent = json.loads(res).get("intent", "CHITCHAT")
                    if intent == "CHITCHAT":
                        ans = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": "You are NEXUS. Concise & Pro."}, {"role": "user", "content": last_query}], max_tokens=100).choices[0].message.content
                        st.session_state.messages.append({"role": "assistant", "content": ans})
                    else:
                        history = sql_bot.load_memory(st.session_state.session_id)
                        sql = sql_bot.generator_node(last_query, history)
                        res_db = sql_bot.executor_node(sql)
                        ans = sql_bot.responder_node(last_query, res_db.get("data", []))
                        ev = sql_bot.evaluation_node(last_query, sql, res_db.get("data", []), ans)
                        sql_bot.save_memory(last_query, ans, st.session_state.session_id)
                        st.session_state.messages.append({"role": "assistant", "content": ans, "eval": ev})
                else:
                    # SECURE NEO4J
                    agent = neo_bot.Neo4jAgent()
                    intent = neo_bot.classifier_node(last_query)
                    if "chitchat" in intent:
                        ans = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": "You are NEXUS Graph AI. Concise & Pro."}, {"role": "user", "content": last_query}], max_tokens=100).choices[0].message.content
                        st.session_state.messages.append({"role": "assistant", "content": ans})
                    else:
                        cypher = neo_bot.cypher_generator_node(last_query, [])
                        exec_res = agent.execute_cypher(cypher)
                        data_payload = exec_res.get("data", []) if exec_res.get("status") == "success" else f"Error: {exec_res.get('message')}"
                        ans = neo_bot.responder_node(last_query, data_payload)
                        ev = neo_bot.evaluation_node(last_query, cypher, data_payload, ans)
                        st.session_state.messages.append({"role": "assistant", "content": ans, "eval": ev})
                    agent.close()
                st.rerun()
            except Exception as e: st.error(f"System Error: {e}")

elif page == "📊 Analytics Dashboard":
    st.markdown("<div class='nexus-header'>Analytics</div>", unsafe_allow_html=True)
    st.info("Start a mission in SQL mode to see live metrics.")

elif page == "🏗️ System Architecture":
    st.markdown("<div class='nexus-header'>Architecture</div>", unsafe_allow_html=True)
    st.markdown("<div class='premium-card'><h4>Ecosystem Flow</h4>Frontend (Streamlit) → Brain (Llama 3.3) → Storage (SQL/Graph)</div>", unsafe_allow_html=True)

elif page == "✨ Core Innovations":
    st.markdown("<div class='nexus-header'>Key Features</div>", unsafe_allow_html=True)
    st.markdown("<div class='premium-card'><h4>🤖 SQL Autonomy</h4>Self-correcting SQL generation.</div>", unsafe_allow_html=True)

else:
    st.markdown("<div class='nexus-header'>Project Specs</div>", unsafe_allow_html=True)
    st.markdown("<div class='premium-card'>✅ <b>D1-D5 Complete</b>.</div>", unsafe_allow_html=True)
