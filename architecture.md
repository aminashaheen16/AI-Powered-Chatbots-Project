# 🏗️ NEXUS Project Architecture Diagrams

## 1. Inventory Chatbot (SQL State Machine)
This diagram illustrates the graph-based state machine approach used for the SQL Inventory Bot.

```mermaid
graph TD
    User([User Input]) --> Intent[Intent Classifier]
    Intent -- Chitchat --> Resp[Friendly Responder]
    Intent -- Query --> Gen[SQL Generator Node]
    
    Gen --> Exec[SQL Executor Node]
    Exec -- Success --> Synth[Synthesis Responder]
    Exec -- Error --> Corr[AI Corrector Node]
    
    Corr --> Exec
    
    Synth --> End([Output Result])
    Resp --> End
    
    subgraph Database
        DB[(SQLite Inventory DB)]
    end
    Exec <--> DB
```

---

## 2. Knowledge Graph Agent (Neo4j CRUD)
This diagram illustrates the flow for translating natural language into graph operations.

```mermaid
graph LR
    Input([NL Inquiry/Command]) --> Classify{Intent Classifier}
    
    Classify -- add --> Cypher[Cypher Generator]
    Classify -- inquire --> Cypher
    Classify -- edit --> Cypher
    Classify -- delete --> Cypher
    
    Cypher --> Neo[(Neo4j Database)]
    Neo --> Engine[Synthesis Engine]
    Engine --> Output([NL Summary])
```
