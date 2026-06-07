import json
import os

from src.math.sharp_consensus import get_consensus_lambda

# 1. HARDCODED TEST (The Control)
test_odds = [{"book": "Pinnacle", "odds": {"Over2.5": 1.934, "Under2.5": 1.952}}]
control_lambda = get_consensus_lambda(test_odds)
print(f"CONTROL TEST: {control_lambda}")

# 2. DATA IMPORT TEST (The Variable Trace)
# We want to see what is ACTUALLY inside your data files right now
shard_path = "data/sharps.json"
if os.path.exists(shard_path):
    with open(shard_path) as f:
        data = json.load(f)
        print(f"\nRAW DATA IN {shard_path}:")
        print(json.dumps(data, indent=2))

        # Run the solver on the actual file data
        file_lambda = get_consensus_lambda(data)
        print(f"\nLAMBDA FROM FILE: {file_lambda}")
else:
    print(f"Error: {shard_path} not found.")
