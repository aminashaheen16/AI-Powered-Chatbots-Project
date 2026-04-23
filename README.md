# 🔱 NEXUS: AI-Powered Chatbots Project (v2.0 Advanced)

This repository contains two distinct AI-powered conversational agents designed for terminal-based interaction with SQL and Neo4j databases, now enhanced with Memory, APIs, and Evaluation.

## 🚀 Key Features (New!)
- **Memory (Short & Long Term)**: 
  - SQL Bot persists history in a SQLite `ChatHistory` table.
  - Neo4j Bot persists history using `:Conversation` nodes in the graph.
- **RESTful APIs**: Fast API server to interact with bots programmatically.
- **AI Evaluation**: Real-time evaluation of each response using an LLM-as-a-judge scoring system.

## 🛠️ Setup

### 1. Prerequisites
- Python 3.8+
- Groq API Key
- Neo4j Instance

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Configuration (.env)
```env
GROQ_API_KEY=your_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

---

## 📂 Execution

### 1. Terminal Bots
- **SQL Bot**: `python inventory_bot.py`
- **Neo4j Bot**: `python knowledge_agent.py`

### 2. API Server
```bash
python api_server.py
```
- **Endpoints**:
  - `POST /sql/query`: { "query": "...", "session_id": "user123" }
  - `POST /graph/query`: { "query": "..." }

---

## 🏗️ Architecture
System design with Memory and Evaluation nodes is detailed in [architecture.md](./architecture.md).

## 📝 Project Report
Full details on implementation, evaluation metrics, and API design are in [Project_Report.md](./Project_Report.md).

### 3. Website Interface (Streamlit)
A premium, ChatGPT-like web interface is now available.
- **Features**: Sidebar session management, New Chat, Delete History, and real-time Evaluation badges.
- **Run**:
  ```bash
  streamlit run app.py
  ```
