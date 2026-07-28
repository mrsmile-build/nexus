"""
NEXUS Memory Engine v0.1
"""

class MemoryEngine:
    def __init__(self):
        self.memory = {}

    def store(self, key, value):
        self.memory[key] = value

    def retrieve(self, key):
        return self.memory.get(key)

    def forget(self, key):
        if key in self.memory:
            del self.memory[key]

    def all(self):
        return self.memory
