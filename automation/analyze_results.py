
import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt


# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSV_DIR = os.path.join(BASE_DIR, "results", "csv")
GRAPH_DIR = os.path.join(BASE_DIR, "results", "graphs")

EARLY_RESULTS_FILE = os.path.join(
    CSV_DIR, "all_experiments.csv"
)

AUTOMATED_RESULTS_FILE = os.path.join(
    CSV_DIR, "automated_results.csv"
)

STATUS_FILE = os.path.join(
    CSV_DIR, "experiment_status.csv"
)

MASTER_RESULTS_FILE = os.path.join(
    CSV_DIR, "master_results.csv"
)

REPORT_FILE = os.path.join(
    CSV_DIR, "performance_analysis.txt"
)


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def read_csv(filepath):

    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"File not found: {filepath}"
        )

    with open(filepath, "r", newline="") as file:
        return list(csv.DictReader(file))


def number(value, field):

    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(
            f"Invalid numeric value for {field}: {value}"
        )


def save_csv(filepath, rows, fields):

    with open(filepath, "w", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            extrasaction="ignore"
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# 3. LOAD AND MERGE EXPERIMENT RESULTS
# ============================================================

def load_experiments():

    early_results = read_csv(EARLY_RESULTS_FILE)
    automated_results = read_csv(AUTOMATED_RESULTS_FILE)
    statuses = read_csv(STATUS_FILE)

    # Validate automated experiment completion.
    successful = {
        row["Configuration"]
        for row in statuses
        if row["Status"] == "SUCCESS"
        and row["Return_Code"] == "0"
    }

    failed = [
        row["Configuration"]
        for row in statuses
        if row["Status"] != "SUCCESS"
        or row["Return_Code"] != "0"
    ]

    if failed:
        raise RuntimeError(
            f"Failed automated experiments: {failed}"
        )

    experiments = {}

    # Load initial experiments.
    for row in early_results:

        name = row["Configuration"]

        if name in experiments:
            raise ValueError(
                f"Duplicate configuration: {name}"
            )

        experiments[name] = dict(row)

    # Load automated experiments.
    for row in automated_results:

        name = row["Configuration"]

        if name in experiments:
            raise ValueError(
                f"Duplicate configuration: {name}"
            )

        if name not in successful:
            raise RuntimeError(
                f"Configuration {name} is not marked SUCCESS."
            )

        experiments[name] = dict(row)

    # The experiment design contains 24 configurations.
    if len(experiments) != 24:
        raise ValueError(
            f"Expected 24 configurations, found {len(experiments)}"
        )

    # Validate and convert the common numeric fields.
    required_numeric_fields = [
        "Issue_Width",
        "ROB_Entries",
        "L2_KB",
        "Simulated_Time_s",
        "Total_Cycles",
        "Simulated_Instructions",
        "IPC",
        "CPI"
    ]

    for name, row in experiments.items():

        for field in required_numeric_fields:

            if field not in row or row[field] == "":
                raise ValueError(
                    f"{field} missing for configuration {name}"
                )

            row[field] = number(row[field], field)

        row["Issue_Width"] = int(row["Issue_Width"])
        row["ROB_Entries"] = int(row["ROB_Entries"])
        row["L2_KB"] = int(row["L2_KB"])
        row["Total_Cycles"] = int(row["Total_Cycles"])
        row["Simulated_Instructions"] = int(
            row["Simulated_Instructions"]
        )

        # L1 cache information exists in the initial CSV,
        # but not in the automated CSV. Preserve blanks
        # rather than inventing values.
        for field in ["L1I_KB", "L1D_KB"]:
            if field in row and row[field] != "":
                row[field] = number(row[field], field)

    print(f"Initial experiments: {len(early_results)}")
    print(f"Automated experiments: {len(automated_results)}")
    print(f"Successful automated experiments: {len(successful)}")

    return experiments


# ============================================================
# 4. CALCULATE PERFORMANCE METRICS
# ============================================================

def calculate_metrics(experiments):

    if "Baseline" not in experiments:
        raise ValueError("Baseline configuration not found.")

    baseline = experiments["Baseline"]

    baseline_cycles = baseline["Total_Cycles"]
    baseline_ipc = baseline["IPC"]

    for row in experiments.values():

        current_cycles = row["Total_Cycles"]
        current_ipc = row["IPC"]

        # All configurations use the same 3 GHz clock.
        # Cycle ratios therefore represent simulated
        # execution-time ratios.

        row["Speedup_vs_Baseline"] = (
            baseline_cycles / current_cycles
        )

        row["Cycle_Change_Percent"] = (
            (current_cycles / baseline_cycles) - 1
        ) * 100

        row["IPC_Change_Percent"] = (
            (current_ipc / baseline_ipc) - 1
        ) * 100

    return baseline_cycles, baseline_ipc


# ============================================================
# 5. PARAMETER-WISE ANALYSIS
# ============================================================

def calculate_group_averages(experiments, parameter):

    grouped = defaultdict(list)

    for row in experiments.values():

        value = row[parameter]
        grouped[value].append(row["Total_Cycles"])

    averages = {}

    for value, cycles in grouped.items():

        averages[value] = (
            sum(cycles) / len(cycles)
        )

    return averages


# ============================================================
# 6. GENERATE GRAPHS
# ============================================================

def generate_graphs(experiments):

    os.makedirs(GRAPH_DIR, exist_ok=True)

    # Sort configurations using total cycles.
    rows = sorted(
        experiments.values(),
        key=lambda row: row["Total_Cycles"]
    )

    names = [
        row["Configuration"]
        for row in rows
    ]

    cycles = [
        row["Total_Cycles"]
        for row in rows
    ]

    ipc_values = [
        row["IPC"]
        for row in rows
    ]

    # --------------------------------------------------------

    # --------------------------------------------------------

    # --------------------------------------------------------

    # --------------------------------------------------------
    # GRAPH 1: EXECUTION CYCLE COMPARISON
    # --------------------------------------------------------

    plt.figure(figsize=(13, 10))

    plt.barh(names[::-1], cycles[::-1])

    plt.xlabel("Total CPU Cycles")
    plt.ylabel("Configuration")
    plt.title("Execution Cycle Comparison Across 24 Configurations",
              fontsize=15, fontweight="bold")

    plt.grid(axis="x", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPH_DIR, "execution_time_comparison.png"),
                dpi=300, bbox_inches="tight")
    plt.close()

    # --------------------------------------------------------
    # GRAPH 2: IPC COMPARISON
    # --------------------------------------------------------

    ipc_sorted = sorted(zip(ipc_values, names), reverse=True)

    plt.figure(figsize=(13, 10))
    plt.barh(
        [item[1] for item in ipc_sorted[::-1]],
        [item[0] for item in ipc_sorted[::-1]]
    )

    plt.xlabel("Instructions Per Cycle (IPC)")
    plt.ylabel("Configuration")
    plt.title("IPC Comparison Across 24 Configurations",
              fontsize=15, fontweight="bold")

    plt.grid(axis="x", linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPH_DIR, "ipc_comparison.png"),
                dpi=300, bbox_inches="tight")
    plt.close()

    # --------------------------------------------------------
    # GRAPH 3: ISSUE WIDTH IMPACT
    # --------------------------------------------------------

    issue_averages = calculate_group_averages(experiments, "Issue_Width")
    issue_sizes = sorted(issue_averages.keys())
    issue_cycles = [issue_averages[size] for size in issue_sizes]

    plt.figure(figsize=(9, 6))
    plt.plot(issue_sizes, issue_cycles, marker="o", linewidth=2.5,
             markersize=8)

    for x, y in zip(issue_sizes, issue_cycles):
        plt.annotate(f"{y:,.0f}", (x, y), xytext=(0, 9),
                     textcoords="offset points", ha="center", fontsize=9)

    plt.xlabel("Issue Width")
    plt.ylabel("Average Total CPU Cycles")
    plt.title("Impact of Issue Width on Execution Cycles",
              fontsize=14, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPH_DIR, "issue_width_impact.png"),
                dpi=300, bbox_inches="tight")
    plt.close()

    # --------------------------------------------------------
    # GRAPH 4: ROB SIZE IMPACT
    # --------------------------------------------------------

    rob_averages = calculate_group_averages(experiments, "ROB_Entries")
    rob_sizes = sorted(rob_averages.keys())
    rob_cycles = [rob_averages[size] for size in rob_sizes]

    plt.figure(figsize=(9, 6))
    plt.plot(rob_sizes, rob_cycles, marker="o", linewidth=2.5,
             markersize=8)

    for x, y in zip(rob_sizes, rob_cycles):
        plt.annotate(f"{y:,.0f}", (x, y), xytext=(0, 9),
                     textcoords="offset points", ha="center", fontsize=9)

    plt.xlabel("Reorder Buffer Size (Entries)")
    plt.ylabel("Average Total CPU Cycles")
    plt.title("Impact of ROB Size on Execution Cycles",
              fontsize=14, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPH_DIR, "rob_impact.png"),
                dpi=300, bbox_inches="tight")
    plt.close()

    # --------------------------------------------------------
    # GRAPH 5: L2 CACHE SIZE IMPACT
    # --------------------------------------------------------

    l2_averages = calculate_group_averages(experiments, "L2_KB")
    l2_sizes = sorted(l2_averages.keys())
    l2_cycles = [l2_averages[size] for size in l2_sizes]

    plt.figure(figsize=(9, 6))
    plt.plot(l2_sizes, l2_cycles, marker="o", linewidth=2.5,
             markersize=8)

    for x, y in zip(l2_sizes, l2_cycles):
        plt.annotate(f"{y:,.0f}", (x, y), xytext=(0, 9),
                     textcoords="offset points", ha="center", fontsize=9)

    plt.xlabel("L2 Cache Size (KB)")
    plt.ylabel("Average Total CPU Cycles")
    plt.title("Impact of L2 Cache Size on Execution Cycles",
              fontsize=14, fontweight="bold")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPH_DIR, "l2_cache_impact.png"),
                dpi=300, bbox_inches="tight")
    plt.close()

    print("Five graphs generated successfully.")





# ============================================================
# 7. GENERATE PERFORMANCE ANALYSIS REPORT
# ============================================================

def generate_report(
    experiments,
    baseline_cycles,
    baseline_ipc
):

    rows = sorted(
        experiments.values(),
        key=lambda row: row["Total_Cycles"]
    )

    best = rows[0]
    worst = rows[-1]

    cycle_reduction = (
        (baseline_cycles - best["Total_Cycles"])
        / baseline_cycles
    ) * 100

    issue_averages = calculate_group_averages(
        experiments,
        "Issue_Width"
    )

    rob_averages = calculate_group_averages(
        experiments,
        "ROB_Entries"
    )

    l2_averages = calculate_group_averages(
        experiments,
        "L2_KB"
    )

    with open(REPORT_FILE, "w") as file:

        file.write(
            "MICROARCHITECTURAL DESIGN SPACE EXPLORATION\n"
        )

        file.write("=" * 60 + "\n\n")

        file.write("EXPERIMENT SUMMARY\n")
        file.write("-" * 40 + "\n")

        file.write(
            f"Total configurations analysed: {len(rows)}\n"
        )

        file.write("Successful automated experiments: 20\n")
        file.write("Processor: X86 O3CPU\n")
        file.write("Cores: 1\n")
        file.write("Clock frequency: 3 GHz\n")
        file.write("Workload: 128x128 Matrix Multiplication\n")

        file.write(
            "Parameters: Issue Width, ROB Entries, L2 Cache Size\n\n"
        )

        file.write("BASELINE PERFORMANCE\n")
        file.write("-" * 40 + "\n")

        file.write(
            f"Total cycles: {baseline_cycles:,}\n"
        )

        file.write(
            f"IPC: {baseline_ipc:.6f}\n"
        )

        file.write(
            f"CPI: {experiments['Baseline']['CPI']:.6f}\n\n"
        )

        file.write("BEST CONFIGURATION\n")
        file.write("-" * 40 + "\n")

        file.write(
            f"Name: {best['Configuration']}\n"
        )

        file.write(
            f"Issue width: {best['Issue_Width']}\n"
        )

        file.write(
            f"ROB entries: {best['ROB_Entries']}\n"
        )

        file.write(
            f"L2 cache: {best['L2_KB']} KB\n"
        )

        file.write(
            f"Total cycles: {best['Total_Cycles']:,}\n"
        )

        file.write(
            f"IPC: {best['IPC']:.6f}\n"
        )

        file.write(
            f"CPI: {best['CPI']:.6f}\n"
        )

        file.write(
            f"Speedup: {best['Speedup_vs_Baseline']:.8f}x\n"
        )

        file.write(
            f"Cycle-count reduction: {cycle_reduction:.6f}%\n\n"
        )

        file.write("SLOWEST CONFIGURATION\n")
        file.write("-" * 40 + "\n")

        file.write(
            f"Name: {worst['Configuration']}\n"
        )

        file.write(
            f"Issue width: {worst['Issue_Width']}\n"
        )

        file.write(
            f"ROB entries: {worst['ROB_Entries']}\n"
        )

        file.write(
            f"L2 cache: {worst['L2_KB']} KB\n"
        )

        file.write(
            f"Total cycles: {worst['Total_Cycles']:,}\n"
        )

        file.write(
            f"IPC: {worst['IPC']:.6f}\n\n"
        )

        file.write("TOP 5 CONFIGURATIONS\n")
        file.write("-" * 40 + "\n")

        for index, row in enumerate(rows[:5], start=1):

            file.write(
                f"{index}. {row['Configuration']}\n"
            )

            file.write(
                f"   Cycles: {row['Total_Cycles']:,}\n"
            )

            file.write(
                f"   IPC: {row['IPC']:.6f}\n"
            )

            file.write(
                f"   Speedup: {row['Speedup_vs_Baseline']:.8f}x\n"
            )

        file.write("\nPARAMETER-WISE ANALYSIS\n")
        file.write("-" * 40 + "\n")

        file.write("\n1. ISSUE WIDTH IMPACT\n")

        for size in sorted(issue_averages):

            file.write(
                f"Issue width {size}: "
                f"{issue_averages[size]:,.2f} average cycles\n"
            )

        file.write("\n2. REORDER BUFFER SIZE IMPACT\n")

        for size in sorted(rob_averages):

            file.write(
                f"ROB {size}: "
                f"{rob_averages[size]:,.2f} average cycles\n"
            )

        file.write("\n3. L2 CACHE SIZE IMPACT\n")

        for size in sorted(l2_averages):

            file.write(
                f"L2 {size} KB: "
                f"{l2_averages[size]:,.2f} average cycles\n"
            )

        file.write("\nMETHODOLOGY AND INTERPRETATION\n")
        file.write("-" * 40 + "\n")

        file.write(
            "All configurations use the same 3 GHz clock frequency. "
            "Therefore, total CPU cycles are used for performance "
            "ranking. Cycle-count ratios are equivalent to "
            "execution-time ratios at a fixed clock frequency.\n\n"
        )

        file.write(
            "Parameter-wise averages are calculated across the "
            "complete factorial experiment matrix. Each parameter "
            "value is averaged across the tested values of the "
            "other two parameters. These averages show overall "
            "trends and do not independently explain parameter "
            "interactions.\n\n"
        )

        file.write(
            "The best configuration is ranked by total cycles. "
            "A very small difference from baseline should not be "
            "considered a meaningful performance improvement "
            "without repeated-run validation.\n\n"
        )

        file.write("END OF REPORT\n")

    print("Performance report generated successfully.")


# ============================================================
# 8. MAIN FUNCTION
# ============================================================

def main():

    print("\nStarting gem5 performance analysis...\n")

    os.makedirs(CSV_DIR, exist_ok=True)
    os.makedirs(GRAPH_DIR, exist_ok=True)

    # Load all 24 experiments.
    experiments = load_experiments()

    # Calculate performance metrics.
    baseline_cycles, baseline_ipc = calculate_metrics(
        experiments
    )

    # Sort using total CPU cycles.
    rows = sorted(
        experiments.values(),
        key=lambda row: row["Total_Cycles"]
    )

    # Build a consistent CSV schema.
    base_fields = [
        "Configuration",
        "Issue_Width",
        "ROB_Entries",
        "L1I_KB",
        "L1D_KB",
        "L2_KB",
        "Simulated_Time_s",
        "Total_Cycles",
        "Simulated_Instructions",
        "IPC",
        "CPI",
        "Speedup_vs_Baseline",
        "Cycle_Change_Percent",
        "IPC_Change_Percent"
    ]

    save_csv(
        MASTER_RESULTS_FILE,
        rows,
        base_fields
    )

    best = rows[0]

    print(f"Configurations analysed: {len(rows)}")
    print(f"Best configuration: {best['Configuration']}")

    print(
        f"Baseline cycles: {baseline_cycles:,}"
    )

    print(
        f"Best configuration cycles: "
        f"{best['Total_Cycles']:,}"
    )

    print(
        f"Speedup vs baseline: "
        f"{best['Speedup_vs_Baseline']:.8f}x"
    )

    # Generate graphs.
    generate_graphs(experiments)

    # Generate report.
    generate_report(
        experiments,
        baseline_cycles,
        baseline_ipc
    )

    print("\nANALYSIS COMPLETED SUCCESSFULLY")

    print(f"Master CSV: {MASTER_RESULTS_FILE}")
    print(f"Report: {REPORT_FILE}")
    print(f"Graphs: {GRAPH_DIR}")


if __name__ == "__main__":
    main()
