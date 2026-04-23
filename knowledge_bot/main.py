import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from knowledge_bot.agent import KnowledgeAgent

def main():
    agent = KnowledgeAgent()
    
    print("\n" + "="*30)
    print("Welcome to the Knowledge Graph Chatbot (Neo4j)")
    print("Type 'exit' to quit.")
    print("="*30 + "\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("Bot: Goodbye!")
                break
            
            response = agent.handle_message(user_input)
            print(f"Bot: {response}")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Bot: An unexpected error occurred: {e}")
    
    agent.db.close()

if __name__ == "__main__":
    main()
