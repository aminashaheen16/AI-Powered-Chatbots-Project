import json
from shared.llm_client import LLMClient
from knowledge_bot.graph_db import Neo4jManager

class KnowledgeAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.db = Neo4jManager()

    def classify_intent(self, user_input):
        prompt = f"""
        Classify the user intent for a Knowledge Graph system.
        Intents:
        - add: Storing new facts (e.g., "Add that Cairo is the capital of Egypt")
        - inquire: Searching for information (e.g., "What is the capital of Egypt?")
        - edit: Correcting existing facts (e.g., "Change the population of Cairo to 20 million")
        - delete: Removing outdated or incorrect facts (e.g., "Remove the fact about the moon")
        - chitchat: Greetings or general talk.
        
        User Input: {user_input}
        
        Respond in JSON: {{"intent": "add" | "inquire" | "edit" | "delete" | "chitchat"}}
        """
        res = self.llm.generate_json(prompt)
        return json.loads(res)['intent']

    def generate_cypher(self, user_input, intent):
        prompt = f"""
        Generate a Cypher query for the intent '{intent}' based on the user input.
        User Input: {user_input}
        
        Schema guidelines:
        - Use nodes like (e:Entity {{name: '...'}}) and relationships like -[:RELATIONSHIP_TYPE]->.
        - For 'add', use MERGE or CREATE.
        - For 'inquire', use MATCH and RETURN.
        - For 'edit', use MATCH and SET.
        - For 'delete', use MATCH and DELETE/DETACH DELETE.
        
        Respond ONLY with the Cypher query.
        """
        query = self.llm.generate(prompt)
        return query.replace("```cypher", "").replace("```", "").strip()

    def synthesize_response(self, user_input, results, intent):
        prompt = f"""
        Generate a natural language response summarizing the action or answering the query.
        User Input: {user_input}
        Intent: {intent}
        Database Results: {json.dumps(results)}
        
        Respond naturally.
        """
        return self.llm.generate(prompt)

    def handle_message(self, user_input, history=None):
        intent = self.classify_intent(user_input)
        
        if intent == 'chitchat':
            return self.llm.generate(f"Respond to: {user_input}")
        
        cypher = self.generate_cypher(user_input, intent)
        results = self.db.run_query(cypher)
        
        if isinstance(results, dict) and "error" in results:
            return f"Error executing Cypher: {results['error']}"
        
        return self.synthesize_response(user_input, results, intent)
