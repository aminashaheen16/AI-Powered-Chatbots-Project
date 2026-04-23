# Mid-Project Report: AI-Powered Chatbots
**Developed by: Amina Mohy**
**Date: April 23, 2026**

## 1. Project Overview
This project involves building two specialized AI agents:
1.  **Inventory Chatbot (SQL)**: Interfaces with a relational database to manage enterprise assets using natural language.
2.  **Knowledge Graph Agent (Neo4j)**: Manages and queries a graph database for dynamic factual information.

Both agents are built with a robust state-machine architecture and utilize the Groq Llama 3.3 model for high-performance reasoning.

## 2. Deliverable 1: Inventory Chatbot (SQL)
### Features:
- **Natural Language to SQL**: Translates complex user inquiries into optimized SQLite queries.
- **Intent Recognition**: Distinguished between conversational chitchat (greetings) and database queries.
- **AI Self-Correction**: If a generated SQL query fails, a 'Corrector' node automatically debugs and retries the operation.
- **Business Logic**: Default filtering for "Active" assets, excluding retired or disposed items unless requested.

### Implementation Detail:
The bot follows a graph-based execution flow:
- `Generator`: Creates SQL from user input.
- `Executor`: Runs SQL against `data/inventory.db`.
- `Corrector`: Fixes syntax or schema errors.
- `Responder`: Synthesizes the final result into natural language.

---

## 3. Deliverable 2: Knowledge Graph Agent (Neo4j)
### Features:
- **Intent Classification**: Classifies input into `add`, `inquire`, `edit`, or `delete`.
- **Dynamic Cypher Generation**: Generates graph-specific queries based on classified intent.
- **CRUD Operations**: Directly manages nodes and relationships in Neo4j.
- **Synthesis Engine**: Provides clear, human-readable summaries of graph actions.

### Implementation Detail:
The agent acts as a translation layer between the user and the Cypher query language, ensuring that non-technical users can manage complex data relationships effortlessly.

---

## 4. Architecture Diagrams
Detailed Mermaid diagrams representing the system design and data flow are included in the `architecture.md` file.

## 5. Conclusion
The system successfully bridges the gap between natural language and structured data management, providing a seamless terminal-based interface for enterprise inventory and knowledge management.
