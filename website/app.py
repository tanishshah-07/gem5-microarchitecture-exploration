from pathlib import Path
from io import BytesIO
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CSV_FILE = ROOT / "results/csv/master_results.csv"
GRAPH_DIR = ROOT / "results/graphs"
REPORT_FILE = ROOT / "results/final_results.txt"
SCREENSHOT_DIR = ROOT / "website/assets/terminal"

st.set_page_config(
    page_title="Microarchitecture Explorer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- VISUAL THEME --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --bg: #080d1b;
    --panel: #111a2e;
    --panel2: #17233b;
    --blue: #55a7ff;
    --purple: #a78bfa;
    --cyan: #48d9e8;
    --text: #edf4ff;
    --muted: #a9b8d0;
}

.stApp {
    background:
      radial-gradient(ellipse at 10% 0%, rgba(48,91,165,.22), transparent 38%),
      radial-gradient(ellipse at 90% 10%, rgba(117,70,190,.17), transparent 35%),
      var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.5px;
}
h1 {font-size: 2.45rem !important; font-weight: 700 !important;}
h2 {font-size: 1.65rem !important;}
h3 {font-size: 1.2rem !important;}
p, label, li {color: #d6e2f5;}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #101a30 0%, #0b1222 100%);
    border-right: 1px solid #263858;
}
[data-testid="stSidebar"] * {color: #e5efff;}
.block-container {padding-top: 2rem; padding-bottom: 4rem; max-width: 1450px;}
[data-testid="stMetric"] {
    background: linear-gradient(145deg, #172744, #111a2d);
    border: 1px solid #2b4166;
    border-radius: 15px;
    padding: 18px 20px;
    box-shadow: 0 8px 25px rgba(0,0,0,.16);
}
[data-testid="stMetricLabel"] {color: #a9c4e8 !important;}
[data-testid="stMetricValue"] {color: #f4f8ff !important; font-family: 'Space Grotesk';}
div[data-testid="stButton"] > button,
div[data-testid="stDownloadButton"] > button {
    border: 1px solid #548fe0;
    border-radius: 10px;
    background: linear-gradient(110deg, #2867bd, #6549bd);
    color: white;
    font-weight: 700;
    padding: .55rem 1.1rem;
    transition: .2s ease;
}
div[data-testid="stButton"] > button:hover,
div[data-testid="stDownloadButton"] > button:hover {
    border-color: #83d9ff;
    color: white;
    transform: translateY(-2px);
    box-shadow: 0 5px 18px #2867bd55;
}
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] > div,
div[data-testid="stMultiSelect"] > div {
    background: #17243a;
    border-color: #385276;
    border-radius: 10px;
}
[data-testid="stDataFrame"] {
    border: 1px solid #304565;
    border-radius: 12px;
    overflow: hidden;
}
hr {border-color: #2a3d5b;}
a {color: #75c9ff !important;}
.hero {
    padding: 38px 40px;
    border: 1px solid #466ca4;
    border-radius: 22px;
    background:
      radial-gradient(circle at 85% 15%, #7654bd88, transparent 32%),
      linear-gradient(115deg, #142e55, #182347 60%, #34265b);
    box-shadow: 0 15px 45px #0005;
    margin: 8px 0 25px 0;
}
.hero h1 {color: white !important; margin-bottom: 8px;}
.hero p {font-size: 1.08rem; color: #d9e9ff; margin: 0;}
.eyebrow {
    color: #80dfff;
    text-transform: uppercase;
    font-size: .78rem;
    font-weight: 800;
    letter-spacing: 2px;
    margin-bottom: 10px;
}
.section-card {
    background: linear-gradient(145deg, #15233b, #101a2d);
    border: 1px solid #2c4265;
    padding: 22px;
    border-radius: 16px;
    min-height: 130px;
}
.section-card h3 {color: #a9d5ff; margin-top: 0;}
.section-card p {color: #bdcce2; margin-bottom: 0;}
.tag {
    display: inline-block;
    border: 1px solid #477bb4;
    color: #a9dcff;
    background: #173253;
    padding: 5px 11px;
    border-radius: 30px;
    font-size: .78rem;
    margin: 3px 5px 3px 0;
}
.small-muted {color: #9bacc6; font-size: .9rem;}
[data-testid="stRadio"] label {font-weight: 600;}
[data-testid="stAlert"] {border-radius: 12px;}
</style>
""", unsafe_allow_html=True)


# -------------------- DATA --------------------
@st.cache_data
def load_data():
    if not CSV_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(CSV_FILE)

df = load_data()

if df.empty:
    st.error("Experiment CSV not found or empty. Check results/csv/master_results.csv.")
    st.stop()

required = [
    "Configuration", "Issue_Width", "ROB_Entries",
    "L2_KB", "Total_Cycles", "IPC", "CPI"
]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Missing columns in master_results.csv: {missing}")
    st.stop()

for col in ["Total_Cycles", "IPC", "CPI"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna(subset=["Total_Cycles", "IPC", "CPI"])

baseline_rows = df[df["Configuration"].astype(str).str.lower() == "baseline"]
baseline = baseline_rows.iloc[0] if not baseline_rows.empty else None
best = df.loc[df["Total_Cycles"].idxmin()]

graphs = {
    "Execution Time Comparison": ("execution_time_comparison.png", "Compare the simulated execution time across configurations."),
    "IPC Comparison": ("ipc_comparison.png", "Instructions completed per cycle. Higher IPC is generally better."),
    "Issue Width Impact": ("issue_width_impact.png", "Explore how changing Issue Width affects performance."),
    "ROB Entries Impact": ("rob_impact.png", "Explore the effect of Reorder Buffer size."),
    "L2 Cache Impact": ("l2_cache_impact.png", "Explore the effect of L2 cache capacity."),
    "Issue Width × ROB Interaction": ("interaction_issue_rob.png", "See how Issue Width and ROB size interact."),
    "Issue Width × L2 Interaction": ("interaction_issue_l2.png", "See how Issue Width and L2 cache interact."),
    "ROB × L2 Interaction": ("interaction_rob_l2.png", "See how ROB size and L2 cache interact."),
    "Factorial Effect Contributions": ("factorial_effect_contributions.png", "Compare the measured contributions of experimental factors.")
}


# -------------------- COMMON HELPERS --------------------
def heading(title, subtitle):
    st.markdown(f"<div class='eyebrow'>GEM5 • DESIGN SPACE EXPLORATION</div>", unsafe_allow_html=True)
    st.title(title)
    st.markdown(f"<p class='small-muted'>{subtitle}</p>", unsafe_allow_html=True)
    st.write("")


def metric_card(label, value, detail=""):
    st.markdown(
        f"""<div class="section-card">
        <div class="small-muted">{label}</div>
        <h2 style="font-size:1.8rem;color:#ffffff;margin:8px 0;">{value}</h2>
        <p>{detail}</p></div>""",
        unsafe_allow_html=True
    )


def terminal_image(title, lines):
    """Create a terminal-style evidence image from actual project data."""
    width = 1100
    line_height = 34
    height = 120 + line_height * len(lines)
    img = Image.new("RGB", (width, height), "#0b1220")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 19
        )
        title_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22
        )
    except OSError:
        font = ImageFont.load_default()
        title_font = font

    draw.rounded_rectangle((15, 15, width-15, height-15), radius=18,
                           fill="#101c30", outline="#41628d", width=2)
    draw.rounded_rectangle((15, 15, width-15, 65), radius=18, fill="#1b2b45")
    draw.ellipse((35, 32, 49, 46), fill="#ff6b6b")
    draw.ellipse((59, 32, 73, 46), fill="#ffd166")
    draw.ellipse((83, 32, 97, 46), fill="#55d68b")
    draw.text((125, 26), title, font=title_font, fill="#dceaff")

    y = 88
    for line in lines:
        draw.text((40, y), line[:100], font=font, fill="#7fe0bd")
        y += line_height

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


# -------------------- PAGE NAVIGATION --------------------
def go_to_page(target):
    st.session_state["page_nav"] = target


# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("## ⚡ GEM5 EXPLORER")
    st.markdown("<span class='tag'>X86</span><span class='tag'>O3CPU</span><span class='tag'>24 RUNS</span>", unsafe_allow_html=True)
    st.caption("MICROARCHITECTURE LAB")
    st.divider()

    pages = [
        "Home",
        "Architecture",
        "Experiments",
        "Compare",
        "Visualizations",
        "Analysis & Report",
        "Repository"
    ]

    if "page_nav" not in st.session_state:
        st.session_state["page_nav"] = "Home"

    st.markdown("""
    <style>
    [data-testid="stSidebar"] div[data-testid="stButton"] > button {
        width: 100%;
        text-align: left;
        justify-content: flex-start;
        border: 1px solid transparent;
        border-radius: 9px;
        background: transparent;
        color: #d9e8ff;
        padding: 9px 13px;
        font-size: 16px;
        font-weight: 600;
        box-shadow: none;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
        background: #203653;
        border-color: #385b89;
        color: white;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(100deg, #2867bd, #6549bd);
        border: 1px solid #78baff;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("**EXPLORE PROJECT**")

    for item in pages:
        st.button(
            item,
            key=f"sidebar_nav_{item}",
            type="primary" if st.session_state["page_nav"] == item else "secondary",
            use_container_width=True,
            on_click=go_to_page,
            args=(item,)
        )

    page = st.session_state["page_nav"]

    st.divider()
    st.markdown("**SIMULATION SETUP**")
    st.caption("Simulator · gem5 25.1.0.1")
    st.caption("Architecture · X86")
    st.caption("CPU · O3CPU")
    st.caption("Frequency · 3 GHz")
    st.caption("Workload · 128 × 128 matrix multiplication")
    st.divider()
    st.caption(f"Loaded experiment records: {len(df)}")


# -------------------- HOME --------------------
if page == "Home":
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">COMPUTER ARCHITECTURE • PERFORMANCE LAB</div>
      <h1>Microarchitecture<br>Design-Space Explorer</h1>
      <p>Discover how processor design choices influence performance.
      Explore recorded gem5 experiments, inspect visual results and compare configurations.</p>
      <br>
      <span class="tag">GEM5 SIMULATOR</span>
      <span class="tag">X86 ARCHITECTURE</span>
      <span class="tag">O3 CPU</span>
      <span class="tag">FACTORIAL EXPERIMENT</span>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Project at a glance")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Experiment runs", len(df))
    c2.metric("Issue Width choices", df["Issue_Width"].nunique())
    c3.metric("ROB sizes", df["ROB_Entries"].nunique())
    c4.metric("L2 cache sizes", df["L2_KB"].nunique())

    st.write("")
    st.subheader("Best measured result")
    a, b, c = st.columns(3)
    a.metric("Configuration", str(best["Configuration"]))
    b.metric("Total cycles", f"{best['Total_Cycles']:,.0f}")
    c.metric("IPC", f"{best['IPC']:.6f}")

    if baseline is not None:
        improvement = (baseline["Total_Cycles"] - best["Total_Cycles"]) / baseline["Total_Cycles"] * 100
        st.info(
            f"The lowest-cycle result is {improvement:.6f}% lower in cycle count "
            "than the baseline. This is a very small measured difference."
        )

    st.divider()
    st.subheader("Explore the project")
    cards = st.columns(3)
    items = [
        ("01  Architecture", "Understand the simulated processor and experimental parameters.", "Architecture"),
        ("02  Experiments", "Choose the configurations whose recorded results you want to inspect.", "Experiments"),
        ("03  Compare", "Select multiple configurations and compare their performance.", "Compare"),
        ("04  Visualizations", "Choose individual graphs to explore trends and interactions.", "Visualizations"),
        ("05  Terminal Gallery", "View screenshots and reconstructed evidence from saved results.", "Terminal Gallery"),
        ("06  Analysis & Report", "Read the report and understand the important findings.", "Analysis & Report")
    ]

    for i, (title, desc, target) in enumerate(items):
        with cards[i % 3]:
            st.markdown(
                f"<div class='section-card'><h3>{title}</h3><p>{desc}</p></div>",
                unsafe_allow_html=True
            )
            st.button(
                "Explore section  →",
                key=f"home_nav_{i}",
                use_container_width=True,
                on_click=go_to_page,
                args=(target,)
            )
        if i % 3 == 2:
            st.write("")


# -------------------- ARCHITECTURE --------------------
elif page == "Architecture":
    heading("Architecture & Methodology",
            "Understand the system setup and the experiment design.")

    st.subheader("Simulation environment")
    env = [
        ("Simulator", "gem5 25.1.0.1"),
        ("ISA", "X86"),
        ("CPU model", "Out-of-Order CPU (O3CPU)"),
        ("CPU cores", "1"),
        ("Clock frequency", "3 GHz"),
        ("Workload", "128 × 128 matrix multiplication")
    ]
    cols = st.columns(3)
    for i, (name, value) in enumerate(env):
        with cols[i % 3]:
            metric_card(name, value)

    st.divider()
    st.subheader("Parameters explored")
    p1, p2, p3 = st.columns(3)
    with p1:
        metric_card("Issue Width", "4 and 8", "Number of instructions the CPU can issue in a cycle.")
    with p2:
        metric_card("ROB Entries", "64, 128, 192, 256", "Capacity of the Reorder Buffer.")
    with p3:
        metric_card("L2 Cache", "128, 256, 512 KB", "Second-level cache capacity.")

    st.subheader("Factorial experiment")
    st.latex(r"2 \\times 4 \\times 3 = 24")
    st.write(
        "Every selected value of Issue Width, ROB Entries and L2 Cache "
        "is combined with the other parameter values, producing 24 configurations."
    )

    st.subheader("Performance metrics")
    st.markdown("""
    - **Total Cycles:** Total processor cycles recorded by the simulation.
    - **IPC:** Instructions Per Cycle. A higher value generally indicates better throughput.
    - **CPI:** Cycles Per Instruction. A lower value generally indicates better efficiency.
    - **Simulated Time:** Time reported by the gem5 simulation.
    - **Speedup:** Performance relative to the baseline configuration.
    """)


# -------------------- EXPERIMENTS --------------------
elif page == "Experiments":
    heading("Experiment Explorer",
            "Choose the experiment configurations you want to inspect.")

    names = sorted(df["Configuration"].astype(str).unique().tolist())
    chosen = st.multiselect(
        "Select one or more configurations",
        options=names,
        default=[],
        placeholder="Search and select configurations..."
    )

    if not chosen:
        st.markdown("""
        <div class="section-card">
        <h3>Choose your experiment runs</h3>
        <p>No configurations are selected. Use the selector above to choose
        the specific runs you want to inspect. Nothing is preselected.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        result = df[df["Configuration"].astype(str).isin(chosen)].copy()
        result = result.sort_values("Total_Cycles")
        st.success(f"{len(result)} selected configuration(s)")
        st.dataframe(result, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇ Download selected experiment data",
            result.to_csv(index=False).encode("utf-8"),
            file_name="selected_experiments.csv",
            mime="text/csv"
        )


# -------------------- COMPARE --------------------
elif page == "Compare":
    heading("Configuration Comparison",
            "Select the configurations you want. The website will compare only your selection.")

    names = sorted(df["Configuration"].astype(str).unique().tolist())
    chosen = st.multiselect(
        "Choose at least two configurations",
        options=names,
        default=[],
        placeholder="Select configurations to compare..."
    )

    if len(chosen) < 2:
        st.info("Select at least two configurations to unlock the comparison.")
    else:
        comp = df[df["Configuration"].astype(str).isin(chosen)].copy()
        comp = comp.sort_values("Total_Cycles")
        winner = comp.iloc[0]

        st.success(f"Lowest cycle count in your selection: {winner['Configuration']}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Lowest cycle count", f"{winner['Total_Cycles']:,.0f}")
        m2.metric("Highest IPC", f"{comp['IPC'].max():.6f}")
        m3.metric("Lowest CPI", f"{comp['CPI'].min():.6f}")

        st.subheader("Selected configurations")
        display = [
            "Configuration", "Issue_Width", "ROB_Entries",
            "L2_KB", "Total_Cycles", "IPC", "CPI"
        ]
        for optional in ["Simulated_Time_s", "Speedup_vs_Baseline"]:
            if optional in comp.columns:
                display.append(optional)
        st.dataframe(comp[display], use_container_width=True, hide_index=True)

        st.subheader("Compare performance")
        left, right = st.columns(2)
        with left:
            fig = px.bar(
                comp, x="Configuration", y="Total_Cycles",
                color="Total_Cycles", color_continuous_scale=["#55d9e8", "#5967d8", "#b18cff"],
                title="Total cycles — lower is better"
            )
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", xaxis_tickangle=-35,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig, use_container_width=True)
        with right:
            fig = px.bar(
                comp, x="Configuration", y="IPC",
                color="IPC", color_continuous_scale=["#4e9cff", "#4be0c1"],
                title="IPC — higher is generally better"
            )
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", xaxis_tickangle=-35,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "The lowest-cycle configuration is identified using Total Cycles. "
            "Consider IPC, CPI and simulated time as well before drawing conclusions."
        )


# -------------------- VISUALIZATIONS --------------------
elif page == "Visualizations":
    heading("Visualization Studio",
            "Choose an individual graph. Only the selected visualization will be displayed.")

    graph_name = st.selectbox(
        "Select a graph",
        options=list(graphs.keys()),
        index=None,
        placeholder="Choose which visualization you want to view..."
    )

    if graph_name is None:
        st.markdown("""
        <div class="section-card">
        <h3>Your visualization workspace</h3>
        <p>Select a graph above to view it. All nine project graphs are available,
        but none is opened automatically.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        filename, description = graphs[graph_name]
        image_path = GRAPH_DIR / filename
        st.subheader(graph_name)
        st.caption(description)
        if image_path.exists():
            st.image(str(image_path), use_container_width=True)
            st.download_button(
                "⬇ Download this graph",
                image_path.read_bytes(),
                file_name=filename,
                mime="image/png"
            )
        else:
            st.error(f"Graph file not found: {image_path}")


# -------------------- TERMINAL GALLERY --------------------
elif page == "Terminal Gallery":
    heading("Terminal & Simulation Gallery",
            "Visual evidence from the saved gem5 experiment results.")

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    screenshots = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        screenshots.extend(SCREENSHOT_DIR.glob(ext))

    st.subheader("Original terminal screenshots")
    if screenshots:
        for path in sorted(screenshots):
            st.image(str(path), caption=path.name, use_container_width=True)
    else:
        st.info(
            "No original terminal screenshots were found in "
            "website/assets/terminal/. Add your real terminal screenshots "
            "to that folder and they will appear here."
        )

    st.divider()
    st.subheader("Terminal-style evidence from recorded data")
    st.caption(
        "These are recreated visual evidence cards generated from the actual "
        "project CSV data. They are not photographs or raw screenshots of a terminal."
    )

    top = df.nsmallest(5, "Total_Cycles")
    run_lines = [
        "$ gem5.opt --version",
        "gem5 Simulator System. https://www.gem5.org",
        "Version: 25.1.0.1",
        "",
        "$ Experiment environment",
        "ISA: X86 | CPU: O3CPU | Cores: 1 | Clock: 3 GHz",
        "Workload: 128 x 128 matrix multiplication",
        f"Recorded configurations: {len(df)}"
    ]
    best_lines = [
        "$ Results: best measured configuration",
        f"Configuration: {best['Configuration']}",
        f"Total cycles: {best['Total_Cycles']:,.0f}",
        f"IPC: {best['IPC']:.6f}",
        f"CPI: {best['CPI']:.6f}"
    ]
    table_lines = ["$ Top five configurations by total cycles"]
    for _, row in top.iterrows():
        table_lines.append(
            f"{row['Configuration']}: {row['Total_Cycles']:,.0f} cycles"
        )

    gallery = [
        ("01 • Simulation Environment", run_lines),
        ("02 • Best Recorded Result", best_lines),
        ("03 • Top Five Configurations", table_lines)
    ]
    cols = st.columns(2)
    for i, (title, lines) in enumerate(gallery):
        with cols[i % 2]:
            st.image(terminal_image(title, lines), use_container_width=True)


# -------------------- ANALYSIS & REPORT --------------------
elif page == "Analysis & Report":
    heading("Analysis & Report",
            "Review the measured results and read the consolidated project report.")

    st.subheader("Best measured configuration")
    st.write(f"**{best['Configuration']}**")
    x, y, z = st.columns(3)
    x.metric("Total cycles", f"{best['Total_Cycles']:,.0f}")
    y.metric("IPC", f"{best['IPC']:.6f}")
    z.metric("CPI", f"{best['CPI']:.6f}")

    if baseline is not None:
        change = (best["Total_Cycles"] - baseline["Total_Cycles"]) / baseline["Total_Cycles"] * 100
        st.subheader("Baseline comparison")
        st.write(f"Baseline cycles: **{baseline['Total_Cycles']:,.0f}**")
        st.write(f"Best measured cycles: **{best['Total_Cycles']:,.0f}**")
        st.write(f"Cycle change relative to baseline: **{change:.6f}%**")

    st.divider()
    if REPORT_FILE.exists():
        report = REPORT_FILE.read_text(encoding="utf-8", errors="replace")
        st.subheader("Complete experiment report")
        st.text_area("Report contents", report, height=450)
        st.download_button(
            "⬇ Download final report",
            report,
            file_name="final_results.txt"
        )
    else:
        st.warning("results/final_results.txt was not found.")


# -------------------- REPOSITORY --------------------
elif page == "Repository":
    heading("Project Repository",
            "Source code, experiment data and documentation.")

    st.markdown("""
    <div class="hero">
      <div class="eyebrow">OPEN SOURCE PROJECT</div>
      <h1>Explore the project on GitHub</h1>
      <p>Review the implementation, recorded simulation results and project documentation.</p>
    </div>
    """, unsafe_allow_html=True)

    st.link_button(
        "↗ Open GitHub Repository",
        "https://github.com/tanishshah-07/gem5-microarchitecture-exploration"
    )

    st.subheader("Team & Contributors")
    st.markdown("""
    - **Tanish Shah**: [@tanishshah-07](https://github.com/tanishshah-07)
    - **Mohammad Ali (Member 2)**: [@Ray000i](https://github.com/Ray000i)
    - **Team Member 3**
    """)

    st.subheader("Repository structure")
    st.code(
        "gem5-microarchitecture-exploration/\n"
        "├── results/\n"
        "│   ├── csv/          # Experiment results\n"
        "│   ├── graphs/       # Nine generated graphs\n"
        "│   └── final_results.txt\n"
        "├── website/\n"
        "│   ├── app.py        # Website source\n"
        "│   ├── requirements.txt\n"
        "│   └── assets/       # Website images\n"
        "└── README.md"
    )

st.divider()
st.markdown(
    "<p style='text-align:center;color:#8296b5;font-size:.85rem;'>"
    "GEM5 MICROARCHITECTURE EXPLORATION • X86 • O3CPU • 24 CONFIGURATIONS"
    "</p>",
    unsafe_allow_html=True
)
