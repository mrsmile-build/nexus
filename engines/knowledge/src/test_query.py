from graph import KnowledgeGraph
from query import QueryEngine

kg = KnowledgeGraph(db_path=":memory:")

kg.add_node("Artificial Intelligence")
kg.add_node("Mathematics")
kg.add_node("Physics")

kg.add_edge(
    "Artificial Intelligence",
    "uses",
    "Mathematics"
)

kg.add_edge(
    "Mathematics",
    "supports",
    "Physics"
)

engine = QueryEngine(kg)

print(engine.answer("What uses Mathematics?"))
print(engine.answer("What supports Physics?"))
