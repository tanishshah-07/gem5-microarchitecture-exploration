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

EARLY_FILE = os.path.join(CSV_DIR, "all_experiments.csv")
AUTOMATED_FILE = os.path.join(CSV_DIR, "automated_results.csv")

INTERACTION_CSV = os.path.join(
    CSV_DIR, "interaction_analysis.csv"
)

INTERACTION_REPORT = os.path.join(
    CSV_DIR, "interaction_analysis.txt"
)


# ============================================================
# 2. LOAD EXPERIMENT DATA
# ============================================================

def load_experiments():

    experiments = {}

    for filepath in [EARLY_FILE, AUTOMATED_FILE]:

        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)

        with open(filepath, "r", newline="") as file:

            reader = csv.DictReader(file)

            required = {
                "Configuration",
                "Issue_Width",
                "ROB_Entries",
                "L2_KB",
                "Total_Cycles"
            }

            if not required.issubset(reader.fieldnames or []):
                raise ValueError(
                    f"Missing required columns in {filepath}"
                )

            for row in reader:

                name = row["Configuration"]

                if name in experiments:
                    raise ValueError(
                        f"Duplicate configuration: {name}"
                    )

                try:
                    experiments[name] = {
                        "Issue_Width": int(row["Issue_Width"]),
                        "ROB_Entries": int(row["ROB_Entries"]),
                        "L2_KB": int(row["L2_KB"]),
                        "Total_Cycles": int(row["Total_Cycles"])
                    }
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Invalid numeric data in {name}"
                    )

    if len(experiments) != 24:
        raise ValueError(
            f"Expected 24 configurations, found {len(experiments)}"
        )

    expected = {
        "Issue_Width": {4, 8},
        "ROB_Entries": {64, 128, 192, 256},
        "L2_KB": {128, 256, 512}
    }

    for parameter, values in expected.items():

        actual = {
            row[parameter] for row in experiments.values()
        }

        if actual != values:
            raise ValueError(
                f"Unexpected values for {parameter}: {actual}"
            )

    print(f"Successfully loaded {len(experiments)} configurations.")

    return experiments


# ============================================================
# 3. CALCULATE PAIRWISE INTERACTION AVERAGES
# ============================================================

def calculate_interaction(
    experiments,
    x_parameter,
    series_parameter,
    averaged_parameter
):

    grouped = defaultdict(list)

    for row in experiments.values():

        key = (
            row[x_parameter],
            row[series_parameter]
        )

        grouped[key].append(row["Total_Cycles"])

    results = []

    for key, cycles in sorted(grouped.items()):

        x_value, series_value = key

        results.append({
            "Analysis": f"{x_parameter}_vs_{series_parameter}",
            "X_Parameter": x_parameter,
            "X_Value": x_value,
            "Series_Parameter": series_parameter,
            "Series_Value": series_value,
            "Mean_Cycles": sum(cycles) / len(cycles),
            "Configurations": len(cycles),
            "Averaged_Over": averaged_parameter
        })

    return results


# ============================================================
# 4. VALIDATE INTERACTION RESULTS
# ============================================================

def validate_results(results, expected_count, expected_group_size):

    if len(results) != expected_count:
        raise ValueError(
            f"Expected {expected_count} comparisons, "
            f"found {len(results)}"
        )

    for row in results:

        if row["Configurations"] != expected_group_size:
            raise ValueError(
                f"Unexpected group size: {row}"
            )


# ============================================================
# 5. GENERATE INTERACTION GRAPHS
# ============================================================

def generate_graph(
    results,
    x_parameter,
    series_parameter,
    title,
    filename
):

    x_values = sorted({
        row["X_Value"] for row in results
    })

    series_values = sorted({
        row["Series_Value"] for row in results
    })

    plt.figure(figsize=(11, 7))

    for series_value in series_values:

        y_values = []

        for x_value in x_values:

            matching = [
                row for row in results
                if row["X_Value"] == x_value
                and row["Series_Value"] == series_value
            ]

            if len(matching) != 1:
                raise ValueError(
                    f"Missing or duplicate point: "
                    f"{x_parameter}={x_value}, "
                    f"{series_parameter}={series_value}"
                )

            y_values.append(matching[0]["Mean_Cycles"])

        plt.plot(
            x_values,
            y_values,
            marker="o",
            markersize=9,
            linewidth=2.5,
            label=f"{series_parameter} = {series_value}"
        )

    ax = plt.gca()
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda y, _: f"{y / 1_000_000:.1f}M")
    )

    plt.xlabel(x_parameter.replace("_", " "), fontsize=11)
    plt.ylabel("Average Total CPU Cycles (Millions)", fontsize=11)
    plt.title(title, fontsize=15, fontweight="bold", pad=15)

    plt.legend(
        title=series_parameter.replace("_", " "),
        loc="best",
        frameon=True
    )

    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        os.path.join(GRAPH_DIR, filename),
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()


# ============================================================
# 6. GENERATE INTERACTION REPORT
# ============================================================

def generate_report(all_results):

    analyses = [
        (
            "Issue Width vs ROB Entries",
            "ROB_Entries_vs_Issue_Width"
        ),
        (
            "Issue Width vs L2 Cache",
            "L2_KB_vs_Issue_Width"
        ),
        (
            "ROB Entries vs L2 Cache",
            "L2_KB_vs_ROB_Entries"
        )
    ]

    with open(INTERACTION_REPORT, "w") as file:

        file.write(
            "GEM5 MICROARCHITECTURAL INTERACTION ANALYSIS\n"
        )

        file.write("=" * 65 + "\n\n")

        file.write("EXPERIMENT DESIGN\n")
        file.write("-" * 45 + "\n")

        file.write("Issue width: 4, 8\n")
        file.write("ROB entries: 64, 128, 192, 256\n")
        file.write("L2 cache: 128, 256, 512 KB\n")
        file.write("Total configurations: 24\n\n")

        file.write(
            "Each pairwise interaction is calculated by averaging "
            "over the third parameter in the factorial design.\n\n"
        )

        for title, analysis_name in analyses:

            selected = [
                row for row in all_results
                if row["Analysis"] == analysis_name
            ]

            if not selected:
                raise ValueError(
                    f"No results found for {analysis_name}"
                )

            file.write(title.upper() + "\n")
            file.write("-" * 45 + "\n")

            for row in selected:

                file.write(
                    f"{row['X_Parameter']}={row['X_Value']}, "
                    f"{row['Series_Parameter']}="
                    f"{row['Series_Value']}: "
                    f"{row['Mean_Cycles']:,.2f} average cycles "
                    f"(n={row['Configurations']})\n"
                )

            file.write("\n")

        file.write("HOW TO INTERPRET INTERACTION GRAPHS\n")
        file.write("-" * 45 + "\n")

        file.write(
            "Each line represents one value of the series parameter. "
            "The plotted points are mean cycle counts averaged over "
            "the third parameter.\n\n"
        )

        file.write(
            "Approximately parallel lines suggest that the effect "
            "of one parameter is relatively consistent across the "
            "tested values of the other parameter.\n\n"
        )

        file.write(
            "Lines with noticeably different slopes or crossing "
            "patterns suggest an interaction. This means the effect "
            "of changing one parameter depends on the value of the "
            "other parameter.\n\n"
        )

        file.write(
            "These graphs show marginal interaction trends. "
            "They do not independently establish the physical cause "
            "of observed performance differences.\n\n"
        )

        file.write("END OF INTERACTION ANALYSIS\n")

    print("Interaction report generated successfully.")


# ============================================================
# 7. SAVE INTERACTION CSV
# ============================================================

def save_interaction_csv(all_results):

    fields = [
        "Analysis",
        "X_Parameter",
        "X_Value",
        "Series_Parameter",
        "Series_Value",
        "Mean_Cycles",
        "Configurations",
        "Averaged_Over"
    ]

    with open(INTERACTION_CSV, "w", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(all_results)

    print("Interaction CSV generated successfully.")


# ============================================================
# 8. MAIN FUNCTION
# ============================================================

def main():

    print("\nStarting microarchitectural interaction analysis...\n")

    os.makedirs(CSV_DIR, exist_ok=True)
    os.makedirs(GRAPH_DIR, exist_ok=True)

    experiments = load_experiments()

    # Interaction 1: Issue Width x ROB
    # Average over L2 cache.

    issue_rob = calculate_interaction(
        experiments,
        "ROB_Entries",
        "Issue_Width",
        "L2_KB"
    )

    validate_results(issue_rob, 8, 3)

    generate_graph(
        issue_rob,
        "ROB_Entries",
        "Issue_Width",
        "Interaction: Issue Width and ROB Entries",
        "interaction_issue_rob.png"
    )

    # Interaction 2: Issue Width x L2
    # Average over ROB entries.

    issue_l2 = calculate_interaction(
        experiments,
        "L2_KB",
        "Issue_Width",
        "ROB_Entries"
    )

    validate_results(issue_l2, 6, 4)

    generate_graph(
        issue_l2,
        "L2_KB",
        "Issue_Width",
        "Interaction: Issue Width and L2 Cache",
        "interaction_issue_l2.png"
    )

    # Interaction 3: ROB x L2
    # Average over issue width.

    rob_l2 = calculate_interaction(
        experiments,
        "L2_KB",
        "ROB_Entries",
        "Issue_Width"
    )

    validate_results(rob_l2, 12, 2)

    generate_graph(
        rob_l2,
        "L2_KB",
        "ROB_Entries",
        "Interaction: ROB Entries and L2 Cache",
        "interaction_rob_l2.png"
    )

    all_results = issue_rob + issue_l2 + rob_l2

    if len(all_results) != 26:
        raise ValueError(
            f"Expected 26 comparisons, found {len(all_results)}"
        )

    save_interaction_csv(all_results)
    generate_report(all_results)

    print("\nINTERACTION ANALYSIS COMPLETED")
    print("--------------------------------------")
    print("Configurations analysed:", len(experiments))
    print("Issue Width x ROB comparisons:", len(issue_rob))
    print("Issue Width x L2 comparisons:", len(issue_l2))
    print("ROB x L2 comparisons:", len(rob_l2))
    print("Total interaction comparisons:", len(all_results))
    print("Graphs generated: 3")

    print("\nGenerated files:")
    print(INTERACTION_CSV)
    print(INTERACTION_REPORT)
    print(GRAPH_DIR)


if __name__ == "__main__":
    main()
