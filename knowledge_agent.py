import os
import json
from groq import Groq
from neo4j import GraphDatabase
from dotenv import load_dotenv

# --- CONFIG ---
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

class Neo4jAgent:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
            self.driver.verify_connectivity()
        except Exception as e:
            self.driver = None

    def execute_cypher(self, query, params=None):
        if not self.driver: return {"status": "error", "message": "No connection"}
        try:
            with self.driver.session() as session:
                result = session.run(query, params)
                return {"status": "success", "data": [record.data() for record in result]}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # --- LONG TERM MEMORY (Graph Based) ---
    def save_memory(self, user_input, ai_response):
        cypher = """
        CREATE (c:Conversation {user_input: $ui, ai_response: $ar, timestamp: datetime()})
        """
        self.execute_cypher(cypher, {"ui": user_input, "ar": ai_response})

    def load_memory(self, limit=5):
        cypher = """
        MATCH (c:Conversation)
        RETURN c.user_input as user, c.ai_response as ai
        ORDER BY c.timestamp DESC LIMIT $limit
        """
        res = self.execute_cypher(cypher, {"limit": limit})
        if res["status"] == "success":
            return list(reversed(res["data"]))
        return []

    def close(self):
        if self.driver: self.driver.close()

# --- AGENT NODES ---

def classifier_node(user_input):
    prompt = f"Classify intent for '{user_input}': add, inquire, edit, delete, chitchat. JSON: {{'intent': '...'}}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content).get("intent")

def cypher_generator_node(user_input, history):
    prompt = f"Generate Cypher for '{user_input}'. History: {history}. Respond ONLY raw Cypher."
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a Neo4j expert."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip().replace("```cypher", "").replace("```", "").strip()

def evaluation_node(user_input, cypher, results, response):
    prompt = f"Evaluate Neo4j Agent. Input: {user_input}, Cypher: {cypher}, Result: {results}, Response: {response}. JSON: {{'accuracy': 0-10, 'feedback': '...'}}"
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(res.choices[0].message.content)

# --- MAIN ---

def main():
    agent = Neo4jAgent()
    print("🕸️ NEXUS GRAPH BOT (Neo4j + Graph Memory + Eval)")
    history = agent.load_memory()
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']: break
            
            intent = classifier_node(user_input)
            if intent == "chitchat":
                print("NEXUS: Hello!")
                continue
                
            cypher = cypher_generator_node(user_input, history)
            res = agent.execute_cypher(cypher)
            
            if res["status"] == "success":
                # Synthesis (Simplified for demo)
                ans = f"Action processed successfully. Result: {res['data']}"
                print(f"NEXUS: {ans}")
                
                agent.save_memory(user_input, ans)
                history.append({"user": user_input, "ai": ans})
                
                ev = evaluation_node(user_input, cypher, res["data"], ans)
                print(f"[EVAL] Accuracy: {ev['accuracy']}/10")
        except KeyboardInterrupt: break
    agent.close()

if __name__ == "__main__":
    main()
