"""
NEXUS Core v0.1

Coordinates all NEXUS engines.
"""

from engines.memory.src.memory import MemoryEngine
from engines.knowledge.src.graph import KnowledgeGraph
from engines.planning.src.planner import Planner
from engines.reasoning.src.reasoner import Reasoner


class NEXUS:
    def __init__(self):
        self.memory = MemoryEngine()
        self.knowledge = KnowledgeGraph()
        self.planner = Planner()
        self.reasoner = Reasoner()

    def run(self, goal):
        print("=" * 50)
        print("NEXUS AI")
        print("=" * 50)

        print(f"\nGoal: {goal}")

        # Store goal
        self.memory.store("goal", goal)

        # Create plan
        plan = self.planner.create_plan(goal)

        # Reason
        result = self.reasoner.reason(
            goal=goal,
            knowledge=["Memory", "Knowledge Graph", "Planning"]
        )

        print("\nPlan:")
        for i, step in enumerate(plan["steps"], start=1):
            print(f"{i}. {step}")

        print("\nReasoning:")
        print(result["conclusion"])

        print("\nMemory:")
        print(self.memory.all())

        return result


if __name__ == "__main__":
    nexus = NEXUS()
    nexus.run("Build NEXUS")
