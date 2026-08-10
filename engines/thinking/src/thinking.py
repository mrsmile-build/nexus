"""
NEXUS Thinking Engine v0.1

Implements the pipeline described in engines/thinking/README.md:
Memory -> Knowledge -> Planning -> Reasoning -> Discovery ->
Verification -> Answer.

This is the fifth version. Memory/Knowledge persist; Planning,
Reasoning, Discovery, and Verification all call a real LLM when a
provider key is set and fall back to simple deterministic behaviour
when it isn't. Reasoning's output gets written into the Knowledge
Graph (context lookup uses keyword search, filtered against generic
terms). Verification sees the plan, not just the reasoning in
isolation. New here: LearningEngine -- the last of the originally
named engines to get real code, aside from Tools -- records feedback
on results and surfaces it for related future goals, so a thumbs-down
note actually changes future reasoning instead of sitting unused.
"""

from engines.memory.src.memory import MemoryEngine
from engines.knowledge.src.graph import KnowledgeGraph
from engines.planning.src.planner import Planner
from engines.reasoning.src.reasoner import Reasoner
from engines.discovery.src.discovery import DiscoveryEngine
from engines.verification.src.verifier import Verifier
from engines.learning.src.learning import LearningEngine

# Words too generic to anchor a keyword search -- found from a real
# case where a calculus question containing "formula" pulled in
# "high-clinker Portland formula" from an unrelated cement answer,
# because "formula" is a substring of that node name even though the
# topics have nothing to do with each other. These are structural/
# categorical nouns that show up across any domain's phrasing, not
# specific enough to mean "these two things are actually related."
_GENERIC_TERMS = {
    "formula", "formulas", "method", "methods", "approach", "approaches",
    "process", "processes", "system", "systems", "result", "results",
    "structure", "structures", "model", "models", "technique", "techniques",
    "strategy", "strategies", "solution", "solutions", "tool", "tools",
    "framework", "concept", "concepts", "idea", "ideas", "factor", "factors",
    "aspect", "aspects", "element", "elements", "component", "components",
    "type", "types", "kind", "kinds", "form", "forms", "way", "ways",
    "design", "designs", "study", "studies", "plan", "plans",
}


class ThinkingEngine:
    def __init__(self, memory_db="data/memory.db", knowledge_db="data/knowledge.db"):
        self.memory = MemoryEngine(db_path=memory_db)
        self.knowledge = KnowledgeGraph(db_path=knowledge_db)
        self.planner = Planner()
        self.reasoner = Reasoner()
        self.discovery = DiscoveryEngine()
        self.verifier = Verifier()
        self.learning = LearningEngine(self.memory)

    def think(self, goal):
        # 1. Remember the goal.
        self.memory.store("last_goal", goal)

        # 2. Pull in whatever the knowledge graph already knows that's
        #    related to this goal.
        knowledge_context = self._gather_context(goal)

        # 3. Plan.
        plan = self.planner.create_plan(goal)

        # 3b. Pull in any feedback on related past goals, so a
        #     thumbs-down note actually changes this reasoning
        #     instead of sitting unused in Memory forever.
        feedback = self.learning.relevant_feedback(goal)

        # 4. Reason using whatever knowledge context and feedback is
        #    available.
        result = self.reasoner.reason(goal=goal, knowledge=knowledge_context, feedback=feedback)

        # 4b. Write back whatever entities/relationships the reasoning
        #     actually relied on. Before this, reasoning happened and
        #     then evaporated -- the graph stayed empty forever no
        #     matter how many goals were reasoned about, even though
        #     the reasoning text kept talking about "querying the
        #     Knowledge Graph" as if it already had content. This is
        #     what makes that true over time instead of aspirational.
        for source, relation, target in result.get("relations", []):
            self.knowledge.add_edge(source, relation, target)

        # 5. Verify the reasoning engine actually produced something
        #    plausible -- now checking it against the plan too, not
        #    just in isolation, so a mismatch between the two (same
        #    number treated as different units, say) can actually be
        #    caught instead of silently passing because each half
        #    read fine on its own.
        verification = self.verifier.verify(
            result.get("conclusion"), goal=goal, plan_steps=plan["steps"]
        )

        # 6. Look for follow-on ideas. Discovery now asks the LLM for
        #    genuinely new angles when available, instead of just
        #    templating the plan's own steps back. discover() now
        #    reports its own method too, same as the other three --
        #    it was the one place that could silently fall back with
        #    no visible sign it had happened.
        discovery_result = self.discovery.discover(plan["steps"], goal=goal)
        ideas = discovery_result["ideas"]

        # 7. Remember the outcome so a future run on the same goal has
        #    something to build on.
        self.memory.store(
            f"result::{goal}",
            {
                "plan": plan,
                "conclusion": result["conclusion"],
                "verification": verification,
                "ideas": ideas,
                "discovery_method": discovery_result["method"],
            },
        )

        return {
            "goal": goal,
            "plan": plan,
            "reasoning": result,
            "verification": verification,
            "ideas": ideas,
            "discovery_method": discovery_result["method"],
        }

    def _gather_context(self, goal, limit=15):
        # Exact match first (the same goal asked before).
        if self.knowledge.exists(goal):
            return self.knowledge.related(goal)

        # Otherwise, search by significant words in the goal, so a
        # related-but-differently-worded goal ("cheaper cement" vs.
        # "cement that's 40% cheaper") can still find prior context
        # instead of needing an exact repeat to ever hit.
        found = []
        goal_lower = goal.lower()

        # Check existing whole node names against the goal text first.
        # Catches multi-word or short entities (e.g. "fly ash") that
        # splitting the goal into individual words would miss, since
        # neither "fly" nor "ash" clears the length filter below on
        # its own -- found via a real test case, not hypothesized.
        for node in self.knowledge.nodes:
            node_lower = node.lower()
            if len(node_lower) > 3 and node_lower in goal_lower and node not in found:
                found.append(node)
                for neighbor in self.knowledge.related(node):
                    if neighbor not in found:
                        found.append(neighbor)

        for word in goal.split():
            word = word.strip(".,!?:;\"'()").lower()
            if len(word) <= 3 or word in _GENERIC_TERMS:
                continue
            for node in self.knowledge.search(word):
                if node not in found:
                    found.append(node)
                    for neighbor in self.knowledge.related(node):
                        if neighbor not in found:
                            found.append(neighbor)

        return found[:limit] if found else ["Memory", "Knowledge Graph", "Planning"]

    def close(self):
        self.memory.close()
        self.knowledge.close()
