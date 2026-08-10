"""
Proves MemoryEngine data survives a restart -- not just a single
process's lifetime. test_memory.py uses ":memory:" for a quick demo;
this test uses a real file and two separate connections to it.
"""

import os

from memory import MemoryEngine

TEST_DB = "test_memory_persistence.db"

if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

# "Process" 1: store something, then close the connection.
first = MemoryEngine(db_path=TEST_DB)
first.store("planet", "Earth")
first.close()

# "Process" 2: open the same file fresh, with no memory of the first
# instance. If this still finds the value, persistence is real.
second = MemoryEngine(db_path=TEST_DB)
value = second.retrieve("planet")
assert value == "Earth", f"Value did not survive a restart, got {value!r}"
print("PASS: memory persisted across a restart ->", value)
second.close()

os.remove(TEST_DB)
