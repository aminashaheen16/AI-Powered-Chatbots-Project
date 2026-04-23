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
            print(f"[!] Warning: Could not connect to Neo4j. Error: {e}")
            self.driver = None

    def execute_cypher(self, query):
        if not self.driver:
            return {"status": "error", "message": "Neo4j Connection Error"}
        try:
            with self.driver.session() as session:
                result = session.run(query)
                data = [record.data() for record in result]
                return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def close(self):
        if self.driver:
            self.driver.close()

# --- AGENT NODES ---

def classifier_node(user_input):
    """Classifies intent into specific CRUD actions or chitchat."""
    prompt = f"""
    Classify the user intent for the following input: '{user_input}'
    
    Categories:
    - add: Storing new facts or nodes (e.g., 'Add a new server named X').
    - inquire: Searching for information (e.g., 'Who is the vendor for Y?').
    - edit: Updating existing facts (e.g., 'Change the location of Z to Room 5').
    - delete: Removing facts (e.g., 'Delete the asset A').
    - chitchat: Greetings or general talk.
    
    Respond with JSON: {{'intent': '...'}}
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content).get("intent")

def cypher_generator_node(user_input, intent):
    """Generates Cypher query based on intent and input."""
    prompt = f"""
    Generate a Neo4j Cypher query to perform the '{intent}' action for: '{user_input}'
    
    Guidelines:
    - Use meaningful labels (e.g., :Asset, :Vendor, :Location).
    - For 'inquire', use MATCH and RETURN.
    - For 'add', use MERGE or CREATE.
    - For 'edit', use MATCH and SET.
    - For 'delete', use MATCH and DETACH DELETE.
    - Return ONLY the raw Cypher query. No markdown formatting.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a Neo4j Cypher expert."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip().replace("```cypher", "").replace("```", "").strip()

def corrector_node(failed_cypher, error_message):
    """Self-corrects a failed Cypher query."""
    print(f"\n[AI-CORRECTION] Cypher error: {error_message}. Retrying...")
    prompt = f"""
    The following Cypher query failed:
    QUERY: {failed_cypher}
    ERROR: {error_message}
    
    Fix the query and return ONLY the corrected Cypher. No markdown formatting.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "You are a Cypher debugging expert."},
                  {"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip().replace("```cypher", "").replace("```", "").strip()

def synthesis_engine(user_input, db_results, intent):
    """Synthesizes a natural language response."""
    prompt = f"""
    User Input: {user_input}
    Intent: {intent}
    Database Result: {db_results}
    
    Provide a natural, human-readable response summarizing the result of the action.
    """
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
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                print("NEXUS: Goodbye!")
                break
            
            # 1. Classify
            intent = classifier_node(user_input)
            if intent == "chitchat":
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": "Respond friendly to: " + user_input}]
                ).choices[0].message.content
                print(f"NEXUS: {res}")
                continue
                
            # 2. Generate Cypher
            cypher = cypher_generator_node(user_input, intent)
            print(f"[CYPHER] {cypher}") 
            
            # 3. Execute with Retry
            results = agent.execute_cypher(cypher)
            if results["status"] == "error":
                cypher = corrector_node(cypher, results["message"])
                results = agent.execute_cypher(cypher)
            
            # 4. Synthesize
            if results["status"] == "success":
                answer = synthesis_engine(user_input, results["data"], intent)
                print(f"NEXUS: {answer}")
            else:
                print(f"NEXUS: Persistent error - {results['message']}")

        except KeyboardInterrupt:
            print("\nNEXUS: Goodbye!")
            break
        except Exception as e:
            print(f"NEXUS: Unexpected error - {e}")

    agent.close()

if __name__ == "__main__":
    main()
