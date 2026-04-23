import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from inventory_bot.database import init_db, execute_query

def demo_run():
    print("--- [DEMO MODE: Simulating AI Responses] ---")
    init_db()
    
    questions = [
        "Hi there!", 
        "Show me all active laptops.",
        "How many monitors do we have?"
    ]
    
    mock_responses = {
        "Hi there!": {"intent": "chitchat", "response": "Hello! How can I help you with the inventory today?"},
        "Show me all active laptops.": {
            "intent": "query", 
            "sql": "SELECT name, quantity FROM Assets WHERE category_id = 1 AND status = 'Active';",
            "response": "We have 10 XPS 15 laptops currently active in the Headquarters."
        },
        "How many monitors do we have?": {
            "intent": "query",
            "sql": "SELECT SUM(quantity) FROM Assets WHERE category_id = 2 AND status = 'Active';",
            "response": "There are a total of 5 active monitors in the inventory."
        }
    }

    for q in questions:
        print(f"\nUser: {q}")
        data = mock_responses[q]
        print(f"Bot (Intent): {data['intent']}")
        if data['intent'] == 'query':
            print(f"Bot (SQL Generated): {data['sql']}")
            res = execute_query(data['sql'])
            print(f"Bot (Database Result): {res['data']}")
        print(f"Bot (Final Response): {data['response']}")

if __name__ == "__main__":
    demo_run()
