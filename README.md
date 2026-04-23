# AI-Powered Chatbots (Mid-Project)

This repository contains two AI-powered terminal chatbots:
1. **Inventory Chatbot (SQL)**: Queries an SQLite database using natural language via a LangGraph state machine.
2. **Knowledge Graph Chatbot (Neo4j)**: Manages and queries facts in a Neo4j graph database.

## Project Structure
```
orange/
├── inventory_bot/      # SQL Chatbot logic
├── knowledge_bot/      # Neo4j Chatbot logic
├── shared/             # Common utilities (LLM, Memory, Evaluation)
├── data/               # Local database files
├── docs/               # Architecture diagrams
└── requirements.txt    # Python dependencies
```

## Setup Instructions

### 1. Prerequisites
- Python 3.9+
- SQLite (usually pre-installed with Python)
- Neo4j (Local Desktop or AuraDB)
- Google Gemini API Key

### 2. Installation
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory based on `.env.template`:
   ```bash
   GEMINI_API_KEY=your_gemini_key
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

### 3. Running the Chatbots

#### Inventory Chatbot (SQL)
```bash
python inventory_bot/main.py
```
- Features: Intent parsing, SQL generation, self-correction loop, and "Active" record filtering.

#### Knowledge Graph Chatbot (Neo4j)
```bash
python knowledge_bot/main.py
```
- Features: CRUD operations (add, inquire, edit, delete) using natural language.

## Architecture
Refer to [docs/architecture.md](docs/architecture.md) for detailed Mermaid diagrams illustrating the system flow.

## Evaluation & Memory
- **Memory**: Includes short-term conversation history and long-term fact persistence.
- **Evaluation**: Use `shared/evaluator.py` to run performance tests and accuracy checks.

## Business Rules (SQL Bot)
- The system defaults to querying "Active" records.
- "Disposed" or "Retired" assets are excluded unless explicitly requested.
