"""
Proves KnowledgeGraph data survives a restart -- not just a single
process's lifetime. test_graph.py uses ":memory:" for a quick demo;
this test uses a real file and two separate connections to it.
"""

import os

from graph import KnowledgeGraph

TEST_DB = "test_graph_persistence.db"

if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

# "Process" 1: add an edge, then close the connection.
first = KnowledgeGraph(db_path=TEST_DB)
first.add_edge("Earth", "orbits", "Sun")
first.close()

# "Process" 2: open the same file fresh, with no memory of the first
# instance. If this still finds the edge, persistence is real.
second = KnowledgeGraph(db_path=TEST_DB)
assert second.relation_exists("Earth", "orbits", "Sun"), "Edge did not survive a restart"
print("PASS: graph persisted across a restart ->", second.show())
second.close()

os.remove(TEST_DB)
