import json
import os

MEMORY_PATH = os.path.join(os.path.dirname(__file__), "../data/long_term_memory.json")

class LongTermMemory:
    def __init__(self):
        self.data = self._load()

    def _load(self):
        if os.path.exists(MEMORY_PATH):
            with open(MEMORY_PATH, "r") as f:
                return json.load(f)
        return {"facts": [], "preferences": {}}

    def save_fact(self, fact):
        self.data["facts"].append(fact)
        self._persist()

    def get_facts(self):
        return self.data["facts"]

    def _persist(self):
        os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
        with open(MEMORY_PATH, "w") as f:
            json.dump(self.data, f, indent=4)

class ConversationBuffer:
    def __init__(self, limit=10):
        self.history = []
        self.limit = limit

    def add(self, role, message):
        self.history.append({"role": role, "content": message})
        if len(self.history) > self.limit:
            self.history = self.history[-self.limit:]

    def get_context(self):
        return "\n".join([f"{h['role']}: {h['content']}" for h in self.history])
