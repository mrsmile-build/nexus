from graph import KnowledgeGraph
from infer import InferenceEngine

kg = KnowledgeGraph(db_path=":memory:")

kg.add_node("Artificial Intelligence")
kg.add_node("Mathematics")
kg.add_node("Physics")
kg.add_node("Gravity")

kg.add_edge("Artificial Intelligence", "uses", "Mathematics")
kg.add_edge("Mathematics", "supports", "Physics")
kg.add_edge("Physics", "explains", "Gravity")

engine = InferenceEngine(kg)

print(engine.infer("Artificial Intelligence"))
