"""
NEXUS Knowledge Graph Engine v0.2
"""

class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = []

    def add_node(self, name, data=None):
        if name not in self.nodes:
            self.nodes[name] = data or {}

    def add_edge(self, source, relation, target):
        self.add_node(source)
        self.add_node(target)

        self.edges.append({
            "source": source,
            "relation": relation,
            "target": target
        })

    def neighbors(self, node):
        return [
            edge
            for edge in self.edges
            if edge["source"] == node
        ]

    def related(self, node):
        related = set()

        for edge in self.edges:
            if edge["source"] == node:
                related.add(edge["target"])
            elif edge["target"] == node:
                related.add(edge["source"])

        return sorted(related)

    def search(self, keyword):
        keyword = keyword.lower()

        return sorted([
            node
            for node in self.nodes
            if keyword in node.lower()
        ])

    def exists(self, node):
        return node in self.nodes

    def relation_exists(self, source, relation, target):
        for edge in self.edges:
            if (
                edge["source"] == source and
                edge["relation"] == relation and
                edge["target"] == target
            ):
                return True
        return False

    def remove_node(self, node):
        if node in self.nodes:
            del self.nodes[node]

        self.edges = [
            edge
            for edge in self.edges
            if edge["source"] != node and edge["target"] != node
        ]

    def remove_edge(self, source, relation, target):
        self.edges = [
            edge
            for edge in self.edges
            if not (
                edge["source"] == source and
                edge["relation"] == relation and
                edge["target"] == target
            )
        ]

    def show(self):
        return {
            "nodes": self.nodes,
            "edges": self.edges
        }
