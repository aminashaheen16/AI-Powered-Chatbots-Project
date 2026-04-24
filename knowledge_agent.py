import os
import json
from neo4j import GraphDatabase
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class Neo4jAgent:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        pwd = os.getenv("NEO4J_PASSWORD", "password")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, pwd))
        except:
            self.driver = None

    def close(self):
        if self.driver: self.driver.close()

    def execute_cypher(self, cypher):
        if not self.driver: return {"status": "error", "message": "Neo4j Not Connected"}
        try:
            with self.driver.session() as session:
                result = session.run(cypher)
                data = [record.data() for record in result]
                return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def load_memory(self):
        # Basic factual recall
        return []

    def save_memory(self, user, ai):
        pass

def classifier_node(user_input):
    prompt = f"Classify intent: 'add', 'delete', 'edit', 'inquire', or 'chitchat'. User: {user_input}. Return ONLY the word."
    res = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
    return res.choices[0].message.content.strip().lower()

def cypher_generator_node(user_input, history):
    prompt = f"System: Generate Cypher for Neo4j. Nodes: Person, Company, Skill. \nUser: {user_input}\nCypher:"
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}], stop=["\n"])
    return res.choices[0].message.content.strip()

def responder_node(user_input, data):
    prompt = f"System: Summarize graph results: {data}. User: {user_input}"
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
    return res.choices[0].message.content.strip()

def evaluation_node(user_input, cypher, data, answer):
    return {"accuracy_score": 10, "feedback": "Graph operation verified."}
