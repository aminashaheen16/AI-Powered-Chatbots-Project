import sys
import os

# Add parent directory to path to import shared/inventory_bot modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from inventory_bot.state_machine import inventory_app
from inventory_bot.database import init_db

def main():
    print("Initializing Inventory Database...")
    init_db()
    
    print("\n" + "="*30)
    print("Welcome to the Inventory Chatbot (SQL)")
    print("Type 'exit' to quit.")
    print("="*30 + "\n")
    
    history = []
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Bot: Goodbye!")
                break
            
            initial_state = {
                "user_input": user_input,
                "intent": "",
                "sql_query": "",
                "query_results": None,
                "error": "",
                "history": history,
                "response": "",
                "retry_count": 0
            }
            
            # Execute the graph
            final_state = inventory_app.invoke(initial_state)
            
            print(f"Bot: {final_state['response']}")
            
            # Update history (Simple memory)
            history.append(f"User: {user_input}")
            history.append(f"Bot: {final_state['response']}")
            if len(history) > 10: # Keep last 10 interactions
                history = history[-10:]
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Bot: An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
