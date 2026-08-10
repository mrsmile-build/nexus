from executor import Executor

executor = Executor()

plan = [
    "Learn Python",
    "Build Memory Engine",
    "Build Knowledge Graph",
    "Run Tests"
]

results = executor.execute_plan(plan)

print("Execution Results:")
for item in results:
    print(item)

print()
print("History:")
print(executor.history_log())
