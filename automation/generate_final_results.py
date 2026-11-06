import csv
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
CSV_DIR = ROOT / "results" / "csv"
RESULTS_DIR = ROOT / "results"
OUTPUT = RESULTS_DIR / "final_results.txt"

def read_csv(filename):
    path = CSV_DIR / filename
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))

def read_text(filename):
    path = CSV_DIR / filename
    return path.read_text(encoding="utf-8").strip()

def line(char="=", width=100):
    return char * width

def section(title):
    return f"\n{line()}\n{title.upper()}\n{line('-')}\n"

def fmt_int(value):
    return f"{int(float(value)):,}"

def fmt_float(value, digits=6):
    return f"{float(value):,.{digits}f}"

def write_report():
    master = read_csv("master_results.csv")
    interactions = read_csv("interaction_analysis.csv")

    performance_report = read_text("performance_analysis.txt")
    statistical_report = read_text("statistical_analysis.txt")

    master.sort(key=lambda row: int(float(row["Total_Cycles"])))

    baseline = next(row for row in master if row["Configuration"] == "Baseline")
    best = master[0]
    worst = master[-1]

    total_configs = len(master)
    total_interactions = len(interactions)

    output = []

    output.append(line("="))
    output.append("GEM5 MICROARCHITECTURAL DESIGN SPACE EXPLORATION")
    output.append("CONSOLIDATED EXPERIMENTAL RESULTS")
    output.append(line("="))
    output.append(f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}")
    output.append("Project: Microarchitectural Design Space Exploration Using gem5")
    output.append("Simulator: gem5 25.1.0.1")
    output.append("Architecture: X86")
    output.append("Processor model: O3CPU")
    output.append("CPU cores: 1")
    output.append("Clock frequency: 3 GHz")
    output.append("Workload: 128 x 128 matrix multiplication")
    output.append("Experimental parameters: Issue Width, ROB Entries, L2 Cache Size")

    output.append(section("1. Experiment Overview"))
    output.append(f"Total factorial configurations: {total_configs}")
    output.append("Experimental design: Balanced 2 x 4 x 3 factorial")
    output.append("Issue Width values: 4, 8")
    output.append("ROB Entries values: 64, 128, 192, 256")
    output.append("L2 Cache values: 128 KB, 256 KB, 512 KB")
    output.append("All configurations use the same workload and 3 GHz clock.")
    output.append("Performance ranking is based on total CPU cycles.")

    output.append(section("2. Baseline Performance"))
    output.append(f"Configuration: {baseline['Configuration']}")
    output.append(f"Issue Width: {baseline['Issue_Width']}")
    output.append(f"ROB Entries: {baseline['ROB_Entries']}")
    output.append(f"L2 Cache: {baseline['L2_KB']} KB")
    output.append(f"Total Cycles: {fmt_int(baseline['Total_Cycles'])}")
    output.append(f"Simulated Time: {baseline['Simulated_Time_s']} seconds")
    output.append(f"Instructions: {fmt_int(baseline['Simulated_Instructions'])}")
    output.append(f"IPC: {baseline['IPC']}")
    output.append(f"CPI: {baseline['CPI']}")

    output.append(section("3. Complete Experimental Results"))
    output.append(
        f"{'Rank':<5} {'Configuration':<31} {'Issue':>5} "
        f"{'ROB':>6} {'L2 KB':>7} {'Cycles':>15} {'IPC':>10} {'CPI':>10}"
    )
    output.append(line("-", 100))

    for rank, row in enumerate(master, start=1):
        output.append(
            f"{rank:<5} {row['Configuration']:<31} "
            f"{row['Issue_Width']:>5} {row['ROB_Entries']:>6} "
            f"{row['L2_KB']:>7} {fmt_int(row['Total_Cycles']):>15} "
            f"{fmt_float(row['IPC']):>10} {fmt_float(row['CPI']):>10}"
        )

    output.append(section("4. Best and Worst Configurations"))
    output.append("BEST MEASURED CONFIGURATION")
    output.append(f"Name: {best['Configuration']}")
    output.append(f"Issue Width: {best['Issue_Width']}")
    output.append(f"ROB Entries: {best['ROB_Entries']}")
    output.append(f"L2 Cache: {best['L2_KB']} KB")
    output.append(f"Cycles: {fmt_int(best['Total_Cycles'])}")
    output.append(f"IPC: {best['IPC']}")
    output.append(f"CPI: {best['CPI']}")
    output.append(f"Speedup vs baseline: {float(best['Speedup_vs_Baseline']):.8f}x")

    cycle_change = (
        (int(float(best["Total_Cycles"])) -
         int(float(baseline["Total_Cycles"])))
        / int(float(baseline["Total_Cycles"]))
    ) * 100

    output.append(f"Cycle-count change vs baseline: {cycle_change:.6f}%")
    output.append("")
    output.append("SLOWEST MEASURED CONFIGURATION")
    output.append(f"Name: {worst['Configuration']}")
    output.append(f"Issue Width: {worst['Issue_Width']}")
    output.append(f"ROB Entries: {worst['ROB_Entries']}")
    output.append(f"L2 Cache: {worst['L2_KB']} KB")
    output.append(f"Cycles: {fmt_int(worst['Total_Cycles'])}")
    output.append(f"IPC: {worst['IPC']}")

    output.append(section("5. Parameter-Wise Performance Analysis"))
    output.append(performance_report)

    output.append(section("6. Microarchitectural Interaction Analysis"))
    output.append(f"Total interaction comparisons: {total_interactions}")
    output.append("The following values are mean cycle counts for each parameter pairing.")
    output.append("They are averaged over the third parameter, as indicated.")

    for analysis_name in sorted(set(row["Analysis"] for row in interactions)):
        subset = [row for row in interactions if row["Analysis"] == analysis_name]
        output.append("")
        output.append(f"{analysis_name} ({len(subset)} comparisons)")
        output.append(line("-", 80))
        output.append(
            f"{'X Parameter':<18} {'X Value':>10} "
            f"{'Series Parameter':<20} {'Series Value':>12} "
            f"{'Mean Cycles':>18} {'N':>5}"
        )
        for row in subset:
            output.append(
                f"{row['X_Parameter']:<18} {row['X_Value']:>10} "
                f"{row['Series_Parameter']:<20} {row['Series_Value']:>12} "
                f"{fmt_float(row['Mean_Cycles'], 2):>18} "
                f"{row['Configurations']:>5}"
            )

    output.append(section("7. Factorial Statistical Analysis"))
    output.append(statistical_report)

    output.append(section("8. Repeat-Run Validation"))
    output.append("Baseline and best configuration were each executed three times.")
    output.append("")
    output.append("BASELINE — all three runs produced identical results:")
    output.append("simTicks: 1,232,374,059")
    output.append("Instructions: 8,770,330")
    output.append("Total cycles: 3,700,824")
    output.append("CPI: 0.421971")
    output.append("IPC: 2.369832")
    output.append("")
    output.append("BEST CONFIGURATION — all three runs produced identical results:")
    output.append("simTicks: 1,232,281,818")
    output.append("Instructions: 8,770,330")
    output.append("Total cycles: 3,700,547")
    output.append("CPI: 0.421939")
    output.append("IPC: 2.370009")
    output.append("")
    output.append("The repeated runs were deterministic in this environment.")

    output.append(section("9. Generated Result Files"))
    output.append("CSV data:")
    for filename in sorted(CSV_DIR.glob("*.csv")):
        output.append(f"  - results/csv/{filename.name}")

    output.append("")
    output.append("Graphs:")
    for filename in sorted((RESULTS_DIR / "graphs").glob("*.png")):
        output.append(f"  - results/graphs/{filename.name}")

    output.append("")
    output.append("Analysis scripts:")
    for filename in sorted((ROOT / "automation").glob("*.py")):
        output.append(f"  - automation/{filename.name}")

    output.append(section("10. Overall Conclusion"))
    output.append(
        "A 24-configuration factorial experiment was conducted using gem5 "
        "to explore Issue Width, Reorder Buffer size, and L2 Cache size."
    )
    output.append(
        f"The lowest cycle count was observed for {best['Configuration']}, "
        f"with {fmt_int(best['Total_Cycles'])} cycles."
    )
    output.append(
        f"Compared with the baseline, the measured cycle reduction was "
        f"{abs(cycle_change):.6f}%."
    )
    output.append(
        "The improvement over baseline is extremely small and should not be "
        "interpreted as a substantial performance gain."
    )
    output.append(
        "Factorial effect decomposition indicates that L2 Cache size "
        "accounted for the largest share of cycle variation in this dataset. "
        "These contribution percentages are descriptive, not proof of causality."
    )
    output.append(
        "The experiment demonstrates an automated workflow for generating "
        "configurations, executing gem5 simulations, collecting statistics, "
        "ranking configurations, and analysing parameter interactions."
    )

    output.append("")
    output.append(line("="))
    output.append("END OF CONSOLIDATED RESULTS")
    output.append(line("="))

    OUTPUT.write_text("\n".join(output) + "\n", encoding="utf-8")

    print("FINAL RESULTS FILE GENERATED SUCCESSFULLY")
    print(f"Location: {OUTPUT.relative_to(ROOT)}")
    print(f"Configurations included: {total_configs}")
    print(f"Interaction comparisons included: {total_interactions}")
    print(f"Graphs available: {len(list((RESULTS_DIR / 'graphs').glob('*.png')))}")
    print(f"File size: {OUTPUT.stat().st_size:,} bytes")

if __name__ == "__main__":
    write_report()
