from graph import KnowledgeGraph

kg = KnowledgeGraph()

kg.add_node("Earth")
kg.add_node("Sun")

kg.add_edge("Earth", "orbits", "Sun")

print(kg.show())
