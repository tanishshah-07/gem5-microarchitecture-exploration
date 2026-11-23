
import csv
import os
import itertools
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSV_DIR = os.path.join(BASE_DIR, "results", "csv")
GRAPH_DIR = os.path.join(BASE_DIR, "results", "graphs")

INPUT_FILE = os.path.join(CSV_DIR, "master_results.csv")
OUTPUT_CSV = os.path.join(CSV_DIR, "statistical_analysis.csv")
OUTPUT_REPORT = os.path.join(CSV_DIR, "statistical_analysis.txt")

os.makedirs(GRAPH_DIR, exist_ok=True)

GRAPH_FILE = os.path.join(
    GRAPH_DIR,
    "factorial_effect_contributions.png"
)

# ============================================================
# 2. LOAD AND VALIDATE DATA
# ============================================================

print("\nStarting factorial statistical analysis...\n")

with open(INPUT_FILE, newline="") as file:
    rows = list(csv.DictReader(file))

data = []

for row in rows:
    data.append({
        "issue": int(row["Issue_Width"]),
        "rob": int(row["ROB_Entries"]),
        "l2": int(row["L2_KB"]),
        "cycles": float(row["Total_Cycles"])
    })

expected = list(itertools.product(
    [4, 8],
    [64, 128, 192, 256],
    [128, 256, 512]
))

actual = [
    (d["issue"], d["rob"], d["l2"])
    for d in data
]

if (
    len(data) != 24
    or set(actual) != set(expected)
    or len(set(actual)) != 24
):
    raise ValueError(
        "Expected exactly 24 unique factorial configurations."
    )

print("Dataset validation passed: 24 configurations.")

# ============================================================
# 3. FACTORIAL DESIGN INFORMATION
# ============================================================

grand_mean = np.mean([d["cycles"] for d in data])

factors = {
    "Issue Width": sorted(set(d["issue"] for d in data)),
    "ROB Entries": sorted(set(d["rob"] for d in data)),
    "L2 Cache (KB)": sorted(set(d["l2"] for d in data))
}

factor_keys = {
    "Issue Width": "issue",
    "ROB Entries": "rob",
    "L2 Cache (KB)": "l2"
}

# ============================================================
# 4. CALCULATE MARGINAL MEANS
# ============================================================

marginal_means = {}

for size in range(1, 4):

    for subset in itertools.combinations(
        factor_keys.keys(), size
    ):

        groups = defaultdict(list)

        for d in data:

            key = tuple(
                d[factor_keys[name]]
                for name in subset
            )

            groups[key].append(d["cycles"])

        marginal_means[subset] = {
            key: np.mean(values)
            for key, values in groups.items()
        }


# ============================================================
# 5. CALCULATE FACTORIAL EFFECTS
# ============================================================

effects = {}

for size in range(1, 4):

    for subset in itertools.combinations(
        factor_keys.keys(), size
    ):

        component = {}

        for d in data:

            key = tuple(
                d[factor_keys[name]]
                for name in subset
            )

            # Center every marginal mean around grand mean.
            effect = marginal_means[subset][key] - grand_mean

            # Remove all lower-order factorial effects.
            for lower_size in range(1, size):

                for lower in itertools.combinations(
                    subset, lower_size
                ):

                    lower_key = tuple(
                        d[factor_keys[name]]
                        for name in lower
                    )

                    effect -= effects[lower][lower_key]

            component[key] = effect

        effects[subset] = component

# ============================================================
# 6. CALCULATE SUM OF SQUARES AND CONTRIBUTIONS
# ============================================================

total_ss = sum(
    (d["cycles"] - grand_mean) ** 2
    for d in data
)

results = []

for subset, component in effects.items():

    ss = 0.0

    for d in data:

        key = tuple(
            d[factor_keys[name]]
            for name in subset
        )

        ss += component[key] ** 2

    contribution = (
        (ss / total_ss) * 100
        if total_ss > 0
        else 0
    )

    results.append({
        "Effect": " x ".join(subset),
        "Degrees_of_Freedom": int(np.prod([
            len(factors[name]) - 1
            for name in subset
        ])),
        "Sum_of_Squares": ss,
        "Contribution_Percent": contribution
    })

# ============================================================
# 7. VALIDATE FACTORIAL DECOMPOSITION
# ============================================================

total_contribution = sum(
    result["Contribution_Percent"]
    for result in results
)

print("\nFactorial decomposition validation:")
print(f"Total contribution: {total_contribution:.6f}%")

if not np.isclose(total_contribution, 100.0, atol=0.001):
    raise ValueError(
        "Factorial contributions do not sum to 100%. "
        "Check the decomposition."
    )

print("Factorial decomposition validation passed.")

# ============================================================
# 8. WRITE STATISTICAL CSV
# ============================================================

with open(OUTPUT_CSV, "w", newline="") as file:

    fieldnames = [
        "Effect",
        "Degrees_of_Freedom",
        "Sum_of_Squares",
        "Contribution_Percent"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(results)

# ============================================================
# 9. GENERATE STATISTICAL REPORT
# ============================================================

with open(OUTPUT_REPORT, "w") as file:

    file.write(
        "GEM5 FACTORIAL STATISTICAL ANALYSIS\n"
    )

    file.write("=" * 65 + "\n\n")

    file.write("EXPERIMENT DESIGN\n")
    file.write("-" * 45 + "\n")

    file.write(
        "Design: Balanced 2 x 4 x 3 factorial\n"
    )

    file.write(
        "Issue Width: 4, 8\n"
        "ROB Entries: 64, 128, 192, 256\n"
        "L2 Cache: 128, 256, 512 KB\n"
    )

    file.write("Total configurations: 24\n")

    file.write(
        f"Grand mean cycles: {grand_mean:,.2f}\n\n"
    )

    file.write("FACTORIAL EFFECT CONTRIBUTIONS\n")
    file.write("-" * 45 + "\n")

    sorted_results = sorted(
        results,
        key=lambda x: x["Contribution_Percent"],
        reverse=True
    )

    for result in sorted_results:

        file.write(
            f'{result["Effect"]}: '
            f'{result["Contribution_Percent"]:.4f}% '
            f'of total variation\n'
        )

    file.write(
        f"\nTotal contribution: "
        f"{total_contribution:.4f}%\n"
    )

    file.write("\nSTATISTICAL INTERPRETATION\n")
    file.write("-" * 45 + "\n")

    largest = sorted_results[0]

    file.write(
        f'The largest contribution in this dataset '
        f'is from {largest["Effect"]}, '
        f'accounting for '
        f'{largest["Contribution_Percent"]:.4f}% '
        f'of total cycle variation.\n'
    )

    file.write(
        "\nSTATISTICAL LIMITATIONS\n"
    )

    file.write("-" * 45 + "\n")

    file.write(
        "Each factorial configuration was simulated once.\n"
        "The complete factorial model has no residual "
        "degrees of freedom.\n"
        "Therefore, conventional residual-based significance "
        "tests and p-values cannot be independently estimated.\n"
        "Effect contributions describe variation in this "
        "experimental dataset and do not establish causality.\n"
    )

# ============================================================
# 10. GENERATE FACTORIAL CONTRIBUTION GRAPH
# ============================================================

labels = [
    result["Effect"]
    for result in results
]

values = [
    result["Contribution_Percent"]
    for result in results
]

order = np.argsort(values)

plt.figure(figsize=(13, 8))

bars = plt.barh(
    [labels[i] for i in order],
    [values[i] for i in order]
)

ax = plt.gca()

for bar, value in zip(bars, [values[i] for i in order]):
    ax.text(
        bar.get_width() + 0.3,
        bar.get_y() + bar.get_height() / 2,
        f"{value:.3f}%",
        va="center",
        fontsize=9
    )

plt.xlabel(
    "Contribution to Total Cycle Variation (%)",
    fontsize=11
)

plt.ylabel("Factorial Effect", fontsize=11)

plt.title(
    "Microarchitectural Factorial Effect Contributions",
    fontsize=15,
    fontweight="bold",
    pad=15
)

plt.grid(axis="x", linestyle="--", alpha=0.3)
plt.xlim(0, max(values) * 1.12)
plt.tight_layout()

plt.savefig(
    GRAPH_FILE,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ============================================================
# 11. FINAL SUMMARY
# ============================================================

print("\nFACTORIAL ANALYSIS COMPLETED")
print("-" * 45)

print("Configurations analysed:", len(data))
print("Factorial effects calculated:", len(results))

for result in sorted_results:

    print(
        f'{result["Effect"]}: '
        f'{result["Contribution_Percent"]:.4f}%'
    )

print(
    f"\nTotal contribution: {total_contribution:.6f}%"
)

print("\nGenerated files:")
print(OUTPUT_CSV)
print(OUTPUT_REPORT)
print(GRAPH_FILE)

print("\nANALYSIS COMPLETED SUCCESSFULLY")
