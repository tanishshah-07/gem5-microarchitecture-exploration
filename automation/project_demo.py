import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "results" / "csv"
GRAPH_DIR = ROOT / "results" / "graphs"

def load_csv(filename):
    with (CSV_DIR / filename).open(
        "r", newline="", encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))

def heading(title):
    print("\n" + "=" * 75)
    print(title.center(75))
    print("=" * 75)

def show_summary():
    rows = load_csv("master_results.csv")
    status = load_csv("experiment_status.csv")

    successful = sum(
        1 for row in status
        if row.get("Status", "").upper() == "SUCCESS"
    )

    heading("1. EXPERIMENT SUMMARY")
    print(f"Total configurations       : {len(rows)}")
    print(f"Successful automated runs  : {successful}")
    print("Experimental design        : 2 x 4 x 3 factorial")
    print("Processor                  : X86 O3CPU")
    print("Clock frequency            : 3 GHz")
    print("Workload                   : 128 x 128 Matrix Multiplication")

def show_best():
    rows = load_csv("master_results.csv")
    rows.sort(key=lambda row: int(float(row["Total_Cycles"])))

    best = rows[0]
    baseline = next(row for row in rows if row["Configuration"] == "Baseline")

    heading("2. BEST CONFIGURATION")

    print(f"Configuration : {best['Configuration']}")
    print(f"Issue Width   : {best['Issue_Width']}")
    print(f"ROB Entries   : {best['ROB_Entries']}")
    print(f"L2 Cache      : {best['L2_KB']} KB")
    print(f"Total Cycles  : {int(float(best['Total_Cycles'])):,}")
    print(f"IPC           : {best['IPC']}")
    print(f"CPI           : {best['CPI']}")
    print(f"Speedup       : {float(best['Speedup_vs_Baseline']):.8f}x")

    difference = (
        int(float(baseline["Total_Cycles"]))
        - int(float(best["Total_Cycles"]))
    )

    print(f"\nCycle reduction vs baseline: {difference:,} cycles")
    print("Note: The measured improvement is very small.")

def show_top_five():
    rows = load_csv("master_results.csv")
    rows.sort(key=lambda row: int(float(row["Total_Cycles"])))

    heading("3. TOP FIVE CONFIGURATIONS")
    print(f"{'Rank':<6}{'Configuration':<32}{'Cycles':>16}{'IPC':>12}")
    print("-" * 70)

    for rank, row in enumerate(rows[:5], 1):
        print(
            f"{rank:<6}{row['Configuration']:<32}"
            f"{int(float(row['Total_Cycles'])):>16,}"
            f"{float(row['IPC']):>12.6f}"
        )

def show_interactions():
    rows = load_csv("interaction_analysis.csv")

    heading("4. MICROARCHITECTURAL INTERACTION ANALYSIS")

    analyses = sorted(set(row["Analysis"] for row in rows))

    for analysis in analyses:
        count = sum(1 for row in rows if row["Analysis"] == analysis)
        print(f"{analysis:<40} {count:>3} comparisons")

    print(f"\nTotal interaction comparisons: {len(rows)}")
    print("All three pairwise interactions were evaluated.")

def show_statistics():
    path = CSV_DIR / "statistical_analysis.txt"

    heading("5. FACTORIAL STATISTICAL ANALYSIS")

    print(path.read_text(encoding="utf-8"))

def show_graphs():
    heading("6. GENERATED PERFORMANCE GRAPHS")

    graphs = sorted(GRAPH_DIR.glob("*.png"))

    for index, graph in enumerate(graphs, 1):
        print(f"{index}. {graph.name}")

    print(f"\nTotal graphs available: {len(graphs)}")
    print(f"Graph directory: {GRAPH_DIR}")


def open_graph():
    graphs = sorted(GRAPH_DIR.glob("*.png"))

    heading("7. OPEN A GRAPH IN WINDOWS")

    if not graphs:
        print("No graphs found.")
        return

    for index, graph in enumerate(graphs, 1):
        print(f"{index}. {graph.name}")

    choice = input("\\nEnter graph number (0 to cancel): ").strip()

    if choice == "0":
        return

    if not choice.isdigit() or not 1 <= int(choice) <= len(graphs):
        print("Invalid graph selection.")
        return

    graph = graphs[int(choice) - 1]

    result = subprocess.run(
        ["wslpath", "-w", str(graph)],
        capture_output=True,
        text=True,
        check=True
    )

    subprocess.Popen(["explorer.exe", result.stdout.strip()])
    print(f"Opening: {graph.name}")

def show_final_report():
    path = ROOT / "results" / "final_results.txt"

    heading("7. FINAL CONSOLIDATED REPORT")

    if not path.exists():
        print("Final report not found.")
        return

    print(path.read_text(encoding="utf-8"))

def main():
    while True:
        print("\n")
        print("=" * 65)
        print("       GEM5 MICROARCHITECTURAL DESIGN SPACE EXPLORATION")
        print("                    PROJECT DEMONSTRATION")
        print("=" * 65)
        print("1. Experiment Summary")
        print("2. Best Configuration")
        print("3. Top Five Configurations")
        print("4. Interaction Analysis")
        print("5. Factorial Statistical Analysis")
        print("6. Generated Graphs")
        print("7. Open a Graph in Windows")
        print("8. Display Complete Results Report")
        print("9. Display Everything")
        print("0. Exit")
        print("=" * 65)

        choice = input("Select an option: ").strip()

        actions = {
            "1": show_summary,
            "2": show_best,
            "3": show_top_five,
            "4": show_interactions,
            "5": show_statistics,
            "6": show_graphs,
            "7": open_graph,
            "8": show_final_report,
        }

        if choice == "0":
            print("\nExiting gem5 project demonstration.")
            break

        elif choice == "9":
            for action in (
                show_summary,
                show_best,
                show_top_five,
                show_interactions,
                show_statistics,
                show_graphs,
            ):
                action()

        elif choice in actions:
            actions[choice]()

        else:
            print("Invalid option. Please select 0-9.")

        if choice != "0":
            input("\nPress Enter to return to the main menu...")

if __name__ == "__main__":
    main()
