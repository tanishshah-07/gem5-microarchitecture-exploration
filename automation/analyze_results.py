
import csv
import os
from collections import defaultdict
import matplotlib.pyplot as plt


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EARLY_RESULTS_FILE = os.path.join(
    BASE_DIR, "results", "csv", "all_experiments.csv"
)

AUTOMATED_RESULTS_FILE = os.path.join(
    BASE_DIR, "results", "csv", "automated_results.csv"
)

MASTER_RESULTS_FILE = os.path.join(
    BASE_DIR, "results", "csv", "master_results.csv"
)

ANALYSIS_REPORT_FILE = os.path.join(
    BASE_DIR, "results", "csv", "performance_analysis.txt"
)

GRAPH_DIR = os.path.join(BASE_DIR, "results", "graphs")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def read_csv_file(filepath):
    """Read a CSV file and return its rows as dictionaries."""

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required file not found: {filepath}")

    with open(filepath, "r", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def convert_number(value, field_name):
    """Convert a CSV value into a number with useful error reporting."""

    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(
            f"Invalid value for {field_name}: {value}"
        )


def save_csv(filepath, rows, fields):
    """Save experiment results into a CSV file."""

    with open(filepath, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


# ============================================================
# LOAD AND MERGE EXPERIMENT RESULTS
# ============================================================

def load_experiments():

    early_results = read_csv_file(EARLY_RESULTS_FILE)
    automated_results = read_csv_file(AUTOMATED_RESULTS_FILE)

    experiments = {}

    # Load the four initial experiments.
    for row in early_results:

        name = row["Configuration"]

        if name in experiments:
            raise ValueError(f"Duplicate configuration: {name}")

        experiments[name] = row

    # Load the 20 automated experiments.
    for row in automated_results:

        name = row["Configuration"]

        if name in experiments:
            raise ValueError(f"Duplicate configuration: {name}")

        experiments[name] = row

    if len(experiments) != 24:
        raise ValueError(
            f"Expected 24 unique configurations, "
            f"but found {len(experiments)}."
        )

    # Convert numeric fields.
    numeric_fields = [
        "Simulated_Time_s",
        "Total_Cycles",
        "Instruction_Count",
        "IPC",
        "CPI"
    ]

    for row in experiments.values():

        for field in numeric_fields:
            row[field] = convert_number(row[field], field)

        row["Total_Cycles"] = int(row["Total_Cycles"])
        row["Instruction_Count"] = int(row["Instruction_Count"])

    return experiments


# ============================================================
# PERFORMANCE METRICS
# ============================================================

def calculate_metrics(experiments):

    if "Baseline" not in experiments:
        raise ValueError("Baseline configuration is missing.")

    baseline = experiments["Baseline"]

    baseline_cycles = baseline["Total_Cycles"]
    baseline_ipc = baseline["IPC"]

    for row in experiments.values():

        current_cycles = row["Total_Cycles"]
        current_ipc = row["IPC"]

        # All configurations use the same 3 GHz clock.
        # Therefore, cycle-count ratio is equivalent to
        # simulated execution-time ratio.

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
# GROUP RESULTS BY MICROARCHITECTURAL PARAMETERS
# ============================================================

def calculate_group_averages(experiments, parameter):

    grouped = defaultdict(list)

    for row in experiments.values():

        parameter_value = row[parameter]
        grouped[parameter_value].append(row["Total_Cycles"])

    averages = {}

    for key, values in grouped.items():
        averages[key] = sum(values) / len(values)

    return averages


# ============================================================
# GRAPH GENERATION
# ============================================================

def generate_graphs(experiments):

    os.makedirs(GRAPH_DIR, exist_ok=True)

    # Sort configurations by total cycles.
    rows = sorted(
        experiments.values(),
        key=lambda row: row["Total_Cycles"]
    )

    names = [row["Configuration"] for row in rows]
    cycles = [row["Total_Cycles"] for row in rows]

    # --------------------------------------------------------
    # GRAPH 1: Execution Cycle Comparison
    # --------------------------------------------------------

    plt.figure(figsize=(16, 8))

    plt.bar(range(len(names)), cycles)

    plt.xticks(
        range(len(names)),
        names,
        rotation=75,
        ha="right",
        fontsize=8
    )

    plt.ylabel("Total CPU Cycles")
    plt.xlabel("Configuration")
    plt.title("Execution Cycle Comparison Across 24 Configurations")

    plt.tight_layout()

    plt.savefig(
        os.path.join(GRAPH_DIR, "execution_time_comparison.png"),
        dpi=300
    )

    plt.close()

    # --------------------------------------------------------
    # GRAPH 2: IPC Comparison
    # --------------------------------------------------------

    ipc_values = [row["IPC"] for row in rows]

    plt.figure(figsize=(16, 8))

    plt.bar(range(len(names)), ipc_values)

    plt.xticks(
        range(len(names)),
        names,
        rotation=75,
        ha="right",
        fontsize=8
    )

    plt.ylabel("Instructions Per Cycle (IPC)")
    plt.xlabel("Configuration")
    plt.title("IPC Comparison Across 24 Configurations")

    plt.tight_layout()

    plt.savefig(
        os.path.join(GRAPH_DIR, "ipc_comparison.png"),
        dpi=300
    )

    plt.close()

    # --------------------------------------------------------
    # GRAPH 3: ROB SIZE IMPACT
    # --------------------------------------------------------

    rob_averages = calculate_group_averages(
        experiments,
        "ROB_Entries"
    )

    rob_sizes = sorted(
        rob_averages.keys(),
        key=lambda value: int(value)
    )

    rob_cycles = [rob_averages[size] for size in rob_sizes]

    plt.figure(figsize=(9, 6))

    plt.plot(
        rob_sizes,
        rob_cycles,
        marker="o"
    )

    plt.xlabel("Reorder Buffer Size (Entries)")
    plt.ylabel("Average Total CPU Cycles")
    plt.title("Impact of ROB Size on Average Execution Cycles")

    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        os.path.join(GRAPH_DIR, "rob_impact.png"),
        dpi=300
    )

    plt.close()

    # --------------------------------------------------------
    # GRAPH 4: L2 CACHE SIZE IMPACT
    # --------------------------------------------------------

    l2_averages = calculate_group_averages(
        experiments,
        "L2_Cache_KB"
    )

    l2_sizes = sorted(
        l2_averages.keys(),
        key=lambda value: int(value)
    )

    l2_cycles = [l2_averages[size] for size in l2_sizes]

    plt.figure(figsize=(9, 6))

    plt.plot(
        l2_sizes,
        l2_cycles,
        marker="o"
    )

    plt.xlabel("L2 Cache Size (KB)")
    plt.ylabel("Average Total CPU Cycles")
    plt.title("Impact of L2 Cache Size on Average Execution Cycles")

    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        os.path.join(GRAPH_DIR, "l2_cache_impact.png"),
        dpi=300
    )

    plt.close()

    print("All four graphs generated successfully.")


# ============================================================
# GENERATE PERFORMANCE ANALYSIS REPORT
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

    best = min(
        rows,
        key=lambda row: row["Total_Cycles"]
    )

    worst = max(
        rows,
        key=lambda row: row["Total_Cycles"]
    )

    cycle_reduction = (
        (baseline_cycles - best["Total_Cycles"])
        / baseline_cycles
    ) * 100

    rob_averages = calculate_group_averages(
        experiments,
        "ROB_Entries"
    )

    l2_averages = calculate_group_averages(
        experiments,
        "L2_Cache_KB"
    )

    issue_averages = calculate_group_averages(
        experiments,
        "Issue_Width"
    )

    with open(ANALYSIS_REPORT_FILE, "w") as file:

        file.write("=" * 65 + "\n")
        file.write("GEM5 MICROARCHITECTURAL DESIGN SPACE EXPLORATION\n")
        file.write("PERFORMANCE ANALYSIS REPORT\n")
        file.write("=" * 65 + "\n\n")

        file.write("EXPERIMENT SUMMARY\n")
        file.write("-" * 65 + "\n")

        file.write(
            f"Total configurations analysed: {len(experiments)}\n"
        )

        file.write("Processor model: X86 O3CPU\n")
        file.write("Number of cores: 1\n")
        file.write("Clock frequency: 3 GHz\n")
        file.write("Workload: 128x128 Matrix Multiplication\n")

        file.write(
            "Parameters: Issue Width, ROB Entries, L2 Cache Size\n\n"
        )

        file.write("PERFORMANCE RANKING\n")
        file.write("-" * 65 + "\n")

        for index, row in enumerate(rows, start=1):

            file.write(
                f"{index:02d}. {row['Configuration']}\n"
            )

            file.write(
                f"    Cycles: {row['Total_Cycles']:,}\n"
            )

            file.write(
                f"    IPC: {row['IPC']:.6f}\n"
            )

            file.write(
                f"    Speedup vs Baseline: "
                f"{row['Speedup_vs_Baseline']:.6f}x\n\n"
            )

        file.write("BEST CONFIGURATION\n")
        file.write("-" * 65 + "\n")

        file.write(
            f"Configuration: {best['Configuration']}\n"
        )

        file.write(
            f"Total cycles: {best['Total_Cycles']:,}\n"
        )

        file.write(
            f"Baseline cycles: {baseline_cycles:,}\n"
        )

        file.write(
            f"IPC: {best['IPC']:.6f}\n"
        )

        file.write(
            f"Speedup vs Baseline: "
            f"{best['Speedup_vs_Baseline']:.6f}x\n"
        )

        file.write(
            f"Cycle-count reduction vs Baseline: "
            f"{cycle_reduction:.6f}%\n\n"
        )

        file.write("WORST CONFIGURATION\n")
        file.write("-" * 65 + "\n")

        file.write(
            f"Configuration: {worst['Configuration']}\n"
        )

        file.write(
            f"Total cycles: {worst['Total_Cycles']:,}\n"
        )

        file.write(
            f"IPC: {worst['IPC']:.6f}\n\n"
        )

        file.write("PARAMETER-WISE ANALYSIS\n")
        file.write("-" * 65 + "\n")

        file.write("\n1. ISSUE WIDTH IMPACT\n")

        for size in sorted(issue_averages, key=lambda x: int(x)):

            file.write(
                f"Issue Width {size}: "
                f"{issue_averages[size]:,.2f} average cycles\n"
            )

        file.write("\n2. REORDER BUFFER SIZE IMPACT\n")

        for size in sorted(rob_averages, key=lambda x: int(x)):

            file.write(
                f"ROB {size}: "
                f"{rob_averages[size]:,.2f} average cycles\n"
            )

        file.write("\n3. L2 CACHE SIZE IMPACT\n")

        for size in sorted(l2_averages, key=lambda x: int(x)):

            file.write(
                f"L2 {size} KB: "
                f"{l2_averages[size]:,.2f} average cycles\n"
            )

        file.write("\nMETHODOLOGY AND INTERPRETATION\n")
        file.write("-" * 65 + "\n")

        file.write(
            "All configurations use the same 3 GHz clock frequency. "
            "Therefore, total cycle count is used for performance "
            "ranking, and the cycle-count ratio is equivalent to "
            "the simulated execution-time ratio.\n\n"
        )

        file.write(
            "Parameter-wise averages are calculated over the complete "
            "factorial experiment matrix. Each parameter value is "
            "averaged across the tested values of the other parameters. "
            "These averages describe overall trends and do not by "
            "themselves explain interactions between parameters.\n\n"
        )

        file.write(
            "The best configuration should not be interpreted as a "
            "meaningful improvement unless repeated runs confirm the "
            "difference. Small cycle-count differences may be negligible "
            "in practical terms.\n\n"
        )

        file.write("END OF REPORT\n")

    print("Performance analysis report generated successfully.")


# ============================================================
# MAIN FUNCTION
# ============================================================

def main():

    print("\nStarting gem5 performance analysis...\n")

    experiments = load_experiments()

    baseline_cycles, baseline_ipc = calculate_metrics(
        experiments
    )

    # Save master CSV.
    fields = list(next(iter(experiments.values())).keys())

    fields.extend([
        "Speedup_vs_Baseline",
        "Cycle_Change_Percent",
        "IPC_Change_Percent"
    ])

    # Avoid duplicate CSV columns.
    fields = list(dict.fromkeys(fields))

    rows = sorted(
        experiments.values(),
        key=lambda row: row["Total_Cycles"]
    )

    save_csv(
        MASTER_RESULTS_FILE,
        rows,
        fields
    )

    print(f"Configurations analysed: {len(rows)}")

    best = rows[0]

    print(
        f"Best configuration: {best['Configuration']}"
    )

    print(
        f"Baseline cycles: {baseline_cycles:,}"
    )

    print(
        f"Best configuration cycles: {best['Total_Cycles']:,}"
    )

    print(
        f"Speedup vs baseline: "
        f"{best['Speedup_vs_Baseline']:.6f}x"
    )

    generate_graphs(experiments)

    generate_report(
        experiments,
        baseline_cycles,
        baseline_ipc
    )

    print("\nANALYSIS COMPLETED SUCCESSFULLY")
    print(f"Master CSV: {MASTER_RESULTS_FILE}")
    print(f"Report: {ANALYSIS_REPORT_FILE}")
    print(f"Graphs: {GRAPH_DIR}")


if __name__ == "__main__":
    main()
o

