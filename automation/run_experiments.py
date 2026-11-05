
import csv
import os
import re
import subprocess
import argparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GEM5 = os.path.expanduser("~/gem5/build/X86/gem5.opt")
CONFIG = os.path.join(PROJECT_ROOT, "configs/x86_experiment_config.py")
PLAN = os.path.join(PROJECT_ROOT, "results/csv/experiment_plan.csv")

RESULTS_FILE = os.path.join(
    PROJECT_ROOT, "results/csv/automated_results.csv"
)
STATUS_FILE = os.path.join(
    PROJECT_ROOT, "results/csv/experiment_status.csv"
)
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")

parser = argparse.ArgumentParser()
parser.add_argument("--limit", type=int, default=0)
args = parser.parse_args()

os.makedirs(LOG_DIR, exist_ok=True)

with open(PLAN, newline="") as file:
    experiments = list(csv.DictReader(file))

if args.limit > 0:
    experiments = experiments[:args.limit]

result_fields = [
    "Configuration",
    "Issue_Width",
    "ROB_Entries",
    "L2_KB",
    "Simulated_Time_s",
    "Total_Cycles",
    "Simulated_Instructions",
    "IPC",
    "CPI",
]

status_fields = ["Configuration", "Status", "Return_Code"]

# Preserve results from previous runs.
existing_results = []
if os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, newline="") as file:
        existing_results = list(csv.DictReader(file))

existing_status = []
if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, newline="") as file:
        existing_status = list(csv.DictReader(file))

result_names = {row["Configuration"] for row in existing_results}
status_names = {row["Configuration"] for row in existing_status}

for exp in experiments:
    name = exp["Configuration"]

    if name in result_names:
        print(f"\nSkipping completed experiment: {name}")
        continue

    issue = int(exp["Issue_Width"])
    rob = int(exp["ROB_Entries"])
    l2 = int(exp["L2_KB"])

    output_dir = os.path.join(PROJECT_ROOT, f"m5out_{name}")
    log_file = os.path.join(LOG_DIR, f"{name}.log")

    # Do not overwrite an existing simulation directory.
    if os.path.exists(output_dir):
        print(f"\nOutput directory already exists: {output_dir}")
        print("Skipping to protect existing simulation data.")
        continue

    command = [
        GEM5,
        "-d", output_dir,
        CONFIG,
        "--issue-width", str(issue),
        "--rob-entries", str(rob),
        "--l2-kb", str(l2),
    ]

    print(f"\nRunning experiment: {name}")
    print(f"Issue={issue}, ROB={rob}, L2={l2} KiB")

    with open(log_file, "w") as log:
        process = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )

    status = "FAILED"

    if process.returncode == 0:
        stats_file = os.path.join(output_dir, "stats.txt")

        if os.path.exists(stats_file):
            with open(stats_file) as file:
                stats = file.read()

            def extract(pattern):
                match = re.search(pattern, stats, re.MULTILINE)
                return match.group(1) if match else ""

            row = {
                "Configuration": name,
                "Issue_Width": issue,
                "ROB_Entries": rob,
                "L2_KB": l2,
                "Simulated_Time_s": extract(
                    r"^simSeconds\s+(\S+)"
                ),
                "Total_Cycles": extract(
                    r"^board\.processor\.cores\.core\.numCycles\s+(\S+)"
                ),
                "Simulated_Instructions": extract(
                    r"^simInsts\s+(\S+)"
                ),
                "IPC": extract(
                    r"^board\.processor\.cores\.core\.ipc\s+(\S+)"
                ),
                "CPI": extract(
                    r"^board\.processor\.cores\.core\.cpi\s+(\S+)"
                ),
            }

            if all(row[key] != "" for key in result_fields[4:]):
                existing_results.append(row)
                result_names.add(name)
                status = "SUCCESS"
            else:
                print("Warning: Some statistics could not be extracted.")
        else:
            print("Warning: stats.txt was not generated.")

    print(f"Result: {status}")

    # Record the status of every attempted experiment.
    existing_status = [
        row for row in existing_status
        if row["Configuration"] != name
    ]

    existing_status.append({
        "Configuration": name,
        "Status": status,
        "Return_Code": process.returncode,
    })

    with open(RESULTS_FILE, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=result_fields)
        writer.writeheader()
        writer.writerows(existing_results)

    with open(STATUS_FILE, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=status_fields)
        writer.writeheader()
        writer.writerows(existing_status)

print("\n===== AUTOMATION SUMMARY =====")
print("Experiments selected:", len(experiments))
print("Successful results:", len(existing_results))
print("Results saved:", RESULTS_FILE)
print("Status saved:", STATUS_FILE)
print("Logs directory:", LOG_DIR)
