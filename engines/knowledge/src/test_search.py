from graph import KnowledgeGraph

kg = KnowledgeGraph(db_path=":memory:")

kg.add_node("Artificial Intelligence")
kg.add_node("Machine Learning")
kg.add_node("Deep Learning")
kg.add_node("Mathematics")
kg.add_node("Physics")

print("Search: Learning")
print(kg.search("Learning"))

print()

print("Search: Math")
print(kg.search("Math"))
