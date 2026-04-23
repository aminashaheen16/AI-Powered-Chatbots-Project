import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from inventory_bot.state_machine import inventory_app
from shared.evaluator import ChatbotEvaluator

def run_evaluation():
    print("--- [Starting Real AI Evaluation] ---")
    evaluator = ChatbotEvaluator(inventory_app)
    
    test_cases = [
        ("Hello, how are you?", ["hello", "how", "help"]),
        ("Show me all active laptops.", ["xps", "laptop", "10"]),
        ("How many monitors do we have in the headquarters?", ["monitor", "5"])
    ]
    
    for query, keywords in test_cases:
        print(f"\nTesting Query: {query}")
        evaluator.evaluate_query(query, keywords)
        last_res = evaluator.results[-1]
        if "error" in last_res:
            print(f"Result: ERROR - {last_res['error']}")
        else:
            print(f"Response: {last_res['response']}")
            print(f"Latency: {last_res['latency']:.2f}s | Passed: {last_res['passed']}")
    
    evaluator.print_report()

if __name__ == "__main__":
    run_evaluation()
