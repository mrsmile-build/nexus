from memory import MemoryEngine

mem = MemoryEngine(db_path=":memory:")

mem.store("planet", "Earth")
mem.store("star", "Sun")

print(mem.retrieve("planet"))
print(mem.retrieve("star"))

mem.forget("planet")

print(mem.all())
