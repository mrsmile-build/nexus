class Reasoner:
    def __init__(self):
        pass

    def reason(self, goal, knowledge):
        return {
            "goal": goal,
            "knowledge_used": knowledge,
            "conclusion": f"Using available knowledge, the next action is to work toward '{goal}'."
        }
