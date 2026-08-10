class QueryEngine:
    def __init__(self, graph):
        self.graph = graph

    def answer(self, question):
        q = question.lower()

        if "what uses mathematics" in q:
            results = []

            for edge in self.graph.edges:
                if (
                    edge["relation"] == "uses"
                    and edge["target"] == "Mathematics"
                ):
                    results.append(edge["source"])

            return results

        if "what supports physics" in q:
            results = []

            for edge in self.graph.edges:
                if (
                    edge["relation"] == "supports"
                    and edge["target"] == "Physics"
                ):
                    results.append(edge["source"])

            return results

        return "I don't know yet."
