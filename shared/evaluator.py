import time

class ChatbotEvaluator:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.results = []

    def evaluate_query(self, query, expected_keywords=None):
        start_time = time.time()
        try:
            # Assuming bot has a handle_message or invoke method
            if hasattr(self.bot, 'invoke'):
                # For LangGraph
                response = self.bot.invoke({"user_input": query})['response']
            else:
                # For Knowledge Agent
                response = self.bot.handle_message(query)
            
            end_time = time.time()
            latency = end_time - start_time
            
            # Simple keyword check
            passed = True
            if expected_keywords:
                for kw in expected_keywords:
                    if kw.lower() not in response.lower():
                        passed = False
                        break
            
            self.results.append({
                "query": query,
                "response": response,
                "latency": latency,
                "passed": passed
            })
            return passed
        except Exception as e:
            self.results.append({"query": query, "error": str(e), "passed": False})
            return False

    def print_report(self):
        print("\n--- Evaluation Report ---")
        total = len(self.results)
        passed = sum(1 for r in self.results if r.get('passed'))
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Accuracy: {(passed/total)*100:.2f}%")
        print("-------------------------\n")
