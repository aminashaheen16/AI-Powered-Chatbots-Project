# 🔱 AI-Powered Chatbots Project (Mid-Project Week 3)

Developed by: **Amina Mohy**

## 📖 Project Overview
This repository contains two distinct AI-powered conversational agents designed to interact with relational (SQL) and graph (Neo4j) databases via a terminal/CLI interface.

---

## 🛠️ Deliverable 1: Inventory Chatbot (SQL)
A terminal-based agent that queries an enterprise relational database using natural language.

### Core Features:
- **Graph-Based State Machine**: Uses Generator, Executor, Corrector, and Responder nodes.
- **AI-Driven Self-Correction**: Automatically fixes syntactically flawed SQL queries.
- **Intent Recognition**: Seamlessly switches between conversational chitchat and database querying.
- **Business Rule Enforcement**: Filters for "Active" records by default.

### Execution:
```bash
python inventory_bot.py
```

---

## 🛠️ Deliverable 2: Knowledge Graph Agent (Neo4j)
An interactive CLI chatbot that translates natural language commands into CRUD operations on a Neo4j graph database.

### Core Features:
- **Multi-Intent Classification**: Supports `add`, `inquire`, `edit`, and `delete` actions.
- **Dynamic Cypher Generation**: Translates NL to structured graph queries.
- **Synthesis Engine**: Provides human-readable summaries of graph modifications and search results.

### Execution:
```bash
python knowledge_agent.py
```

---

## 🏗️ Architecture Diagrams
Architectural Mermaid diagrams are located in the `architecture.md` file, detailing the system design, data flow, and state machine logic for both deliverables.

---

## ⚙️ Setup & Dependencies

### 1. Prerequisites
- Python 3.8+
- SQLite (built-in)
- Neo4j Instance (Local or AuraDB)
- Groq API Key

### 2. Installation
```bash
pip install groq python-dotenv neo4j
```

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_api_key_here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

---

## 📊 Database Schema (SQL)
The system operates on the `Assets` table with the following schema:
- `id` (INT)
- `name` (TEXT)
- `quantity` (INT)
- `status` (TEXT) - e.g., 'Active', 'Inactive', 'Disposed'
- `vendor` (TEXT)
- `location` (TEXT)
