import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

class GraphDB:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        except Exception as e:
            print(f"Warning: Could not connect to Neo4j. Error: {e}")

    def close(self):
        if self.driver:
            self.driver.close()

    def execute_query(self, query, parameters=None):
        if not self.driver:
            raise Exception("Neo4j driver not initialized.")
        
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def run_query(self, query, parameters=None):
        # Compatibility wrapper
        return [record.data() for record in self.execute_query(query, parameters)]
