# 🔱 NEXUS: AI-Powered Chatbots Project

This repository contains two distinct AI-powered conversational agents designed for terminal-based interaction with SQL and Neo4j databases.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8+
- Groq API Key
- Neo4j Instance (Local Desktop or AuraDB)

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

---

## 📂 Deliverables

### 1. Inventory Chatbot (SQL)
- **File**: `inventory_bot.py`
- **Database**: `data/inventory.db` (SQLite)
- **Features**: Intent parsing, Self-correction, Business rule enforcement (Active records).
- **Run**:
  ```bash
  python inventory_bot.py
  ```

### 2. Knowledge Graph Agent (Neo4j)
- **File**: `knowledge_agent.py`
- **Features**: Classifies actions (add, inquire, edit, delete), dynamic Cypher generation, natural language synthesis.
- **Run**:
  ```bash
  python knowledge_agent.py
  ```

---

## 🏗️ Architecture
System design and data flow diagrams are available in [architecture.md](./architecture.md).

## 📊 SQL Schema
The inventory database follows this structure:
- `id` (PK)
- `name` (Asset name)
- `quantity` (Current stock)
- `status` ('Active', 'Inactive', 'Disposed')
- `vendor` (Manufacturer/Vendor)
- `location` (Physical location)

## 📝 Project Report
A comprehensive project summary is available in [Project_Report.md](./Project_Report.md).
