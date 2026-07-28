class InferenceEngine:

    def __init__(self, graph):
        self.graph = graph

    def infer(self, start):
        results = []

        for edge in self.graph.edges:
            if edge["source"] == start:
                target = edge["target"]

                for edge2 in self.graph.edges:
                    if edge2["source"] == target:
                        results.append({
                            "from": start,
                            "through": target,
                            "to": edge2["target"]
                        })

        return results
