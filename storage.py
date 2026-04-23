import sqlite3
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
DB_PATH = 'data/inventory.db'
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

def get_sql_sessions():
    """Returns unique session IDs from SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT session_id FROM ChatHistory ORDER BY timestamp DESC")
        sessions = [row[0] for row in cursor.fetchall()]
        conn.close()
        return sessions
    except:
        return []

def delete_sql_history():
    """Clears all SQL chat history."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ChatHistory")
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_neo4j_sessions():
    """Returns placeholder or unique markers for Neo4j conversations."""
    # Since we don't have explicit session_ids in Neo4j Conversation nodes yet, 
    # we return a list of timestamps or just 'Recent Conversations'
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            result = session.run("MATCH (c:Conversation) RETURN c.timestamp as ts ORDER BY ts DESC LIMIT 10")
            sessions = [str(record["ts"]) for record in result]
        driver.close()
        return sessions
    except:
        return []

def delete_neo4j_history():
    """Clears all Neo4j conversation nodes."""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            session.run("MATCH (c:Conversation) DETACH DELETE c")
        driver.close()
        return True
    except:
        return False
