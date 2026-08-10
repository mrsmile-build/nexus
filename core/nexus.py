"""
NEXUS Core v0.2

Thin entry point. The actual coordination logic that used to live
here now lives in the Thinking Engine (engines/thinking/src/thinking.py),
so the code matches what engines/thinking/README.md already documents.
The NEXUS class/run() method are kept so nothing that already calls
them breaks.
"""

from engines.thinking.src.thinking import ThinkingEngine


class NEXUS:
    def __init__(self):
        self.engine = ThinkingEngine()

    def run(self, goal):
        print("=" * 50)
        print("NEXUS AI")
        print("=" * 50)
        print(f"\nGoal: {goal}")

        outcome = self.engine.think(goal)

        print(f"\nPlan (via {outcome['plan']['method']}):")
        for i, step in enumerate(outcome["plan"]["steps"], start=1):
            print(f"{i}. {step}")

        print(f"\nReasoning (via {outcome['reasoning']['method']}):")
        print(outcome["reasoning"]["conclusion"])

        v = outcome["verification"]
        print(f"\nVerification (via {v['method']}):")
        print(f"  Verified: {v['verified']}")
        if v.get("confidence") is not None:
            print(f"  Confidence: {v['confidence']}")
        if v.get("issues"):
            print(f"  Issues: {', '.join(v['issues'])}")

        print(f"\nDiscovery ideas (via {outcome['discovery_method']}):")
        for idea in outcome["ideas"]:
            print(f"- {idea}")

        print("\nMemory:")
        print(self.engine.memory.all())

        self.engine.close()
        return outcome


if __name__ == "__main__":
    nexus = NEXUS()
    nexus.run("Build NEXUS")
