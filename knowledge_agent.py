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
            print(f"[!] Warning: Could not connect to Neo4j at {NEO4J_URI}. Error: {e}")
            self.driver = None

    def execute_cypher(self, query):
        if not self.driver: return "Neo4j Connection Error"
        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    def close(self):
        if self.driver: self.driver.close()

# --- AGENT LOGIC ---

def classifier_node(user_input):
    """Classifies intent into add, inquire, edit, or delete."""
    prompt = f"Classify intent for: '{user_input}'. Options: add, inquire, edit, delete, chitchat. Respond JSON: {{'intent': '...'}}"
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content).get("intent")

def cypher_generator_node(user_input, intent):
    """Generates Cypher query based on intent."""
    prompt = f"Generate Neo4j Cypher for intent '{intent}' based on: '{user_input}'. Respond ONLY raw Cypher query."
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a Neo4j Cypher expert."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip().replace("```cypher", "").replace("```", "")

def synthesis_engine(user_input, db_results, intent):
    """Generates human-readable summary."""
    prompt = f"Summarize action/result for '{user_input}' with data: {db_results}. Respond naturally."
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# --- MAIN CLI ---

def main():
    agent = Neo4jAgent()
    print("="*50)
    print("🕸️ NEXUS KNOWLEDGE GRAPH AGENT (Neo4j-CLI)")
    print("="*50)
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']: break
        
        # 1. Classify
        intent = classifier_node(user_input)
        if intent == "chitchat":
            print("NEXUS: Hello! How can I help with your Knowledge Graph today?")
            continue
            
        # 2. Generate Cypher
        cypher = cypher_generator_node(user_input, intent)
        print(f"[CYPHER] {cypher}") # Debugging like the image
        
        # 3. Execute
        results = agent.execute_cypher(cypher)
        
        # 4. Synthesize
        answer = synthesis_engine(user_input, results, intent)
        print(f"NEXUS: {answer}")

    agent.close()

if __name__ == "__main__":
    main()
