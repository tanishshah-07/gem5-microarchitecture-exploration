import csv
import os
from itertools import product

# Project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OUTPUT_FILE = os.path.join(
    PROJECT_ROOT,
    "results",
    "csv",
    "experiment_plan.csv"
)

# Parameter values
issue_widths = [4, 8]
rob_entries = [64, 128, 192, 256]
l2_sizes = [128, 256, 512]

# Already completed configurations
completed = {
    (4, 128, 256),
    (4, 192, 256),
    (8, 128, 256),
    (8, 192, 256),
}

experiments = []

for issue, rob, l2 in product(
    issue_widths,
    rob_entries,
    l2_sizes
):
    if (issue, rob, l2) in completed:
        continue

    name = f"issue{issue}_rob{rob}_l2_{l2}KB"

    experiments.append({
        "Configuration": name,
        "Issue_Width": issue,
        "ROB_Entries": rob,
        "L2_KB": l2,
    })

# Write experiment plan
with open(OUTPUT_FILE, "w", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "Configuration",
            "Issue_Width",
            "ROB_Entries",
            "L2_KB",
        ]
    )

    writer.writeheader()
    writer.writerows(experiments)

print("EXPERIMENT PLAN GENERATED")
print("Total configurations:", len(experiments))
print("Output:", OUTPUT_FILE)

for experiment in experiments:
    print(experiment)
