from graph import KnowledgeGraph

kg = KnowledgeGraph(db_path=":memory:")

kg.add_node("Earth")
kg.add_node("Sun")

kg.add_edge("Earth", "orbits", "Sun")

print(kg.show())
