class DiscoveryEngine:

    def discover(self, observations):
        ideas = []

        for item in observations:
            ideas.append(f"Possible improvement: {item}")

        return ideas
