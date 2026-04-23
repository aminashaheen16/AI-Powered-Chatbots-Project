# Advanced AI-Powered Chatbots: Memory, APIs, and Evaluation
**Developed by: Amina Mohy**

## 1. Memory Management
### Short-Term Memory
Maintained through a sliding window of the last 5 interactions within the current execution context. This ensures the LLM has immediate conversational context for follow-up questions (e.g., "What about their locations?").

### Long-Term Memory
- **SQL Bot**: Implemented using a `ChatHistory` table in SQLite. Every user input and AI response is stored with a `session_id`, allowing for cross-session continuity.
- **Neo4j Bot**: Uses a graph-native approach where each interaction is saved as a `:Conversation` node. This allows the graph to learn from its own interaction history.

## 2. API Integration
A FastAPI-based server (`api_server.py`) has been developed to expose the chatbot logic as scalable web services. This allows for:
- Integration with external frontends or mobile apps.
- Multi-user support via `session_id` management.
- Standardized JSON responses including the raw database queries (SQL/Cypher) and evaluation metrics.

## 3. Evaluation Framework
Every turn of the conversation is evaluated by a secondary "Quality Assurance" LLM (Llama 3.1 8B).
- **Metrics**: Accuracy Score (0-10), SQL/Cypher Correctness (boolean), and Qualitative Feedback.
- **Goal**: This framework provides a continuous feedback loop for monitoring the reliability of NL-to-DB translations.

## 4. Technical Stack
- **LLM**: Groq Llama 3.3 (Production) & Llama 3.1 8B (Evaluation).
- **Database**: SQLite & Neo4j.
- **Backend**: FastAPI & Uvicorn.
