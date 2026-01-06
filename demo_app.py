from __future__ import annotations

from pathlib import Path
import os
import time
from typing import Optional

import streamlit as st

from proteomics_app.auth import require_password
from proteomics_app.viewer.chrom_viewer import render_viewer
from proteomics_app.viewer.stats_viewer import render_stats

from types import SimpleNamespace



# -------------------------
# Streamlit config + auth
# -------------------------
st.set_page_config(layout="wide", page_title="Proteomics Pipeline Wizard (Demo)")
require_password("Proteomics Pipeline Wizard (Demo)")

st.title("Proteomics Pipeline Wizard (Demo)")

st.markdown(
    """
This is a **read-only demo** of the wizard UI and analysis tools.

- The **Pipeline** tab is shown for demonstration, but uploads/runs are disabled.
- The **Viewer** and **Stats** tabs are fully interactive and load a preloaded dataset.
"""
)

# -------------------------
# Demo dataset paths
# -------------------------
APP_DIR = Path(__file__).resolve().parent
DEMO_DIR = APP_DIR / "demo_data"

# Update these to match the filenames you place in demo_data/
DEMO_SPLIT_XLSX = DEMO_DIR / "demo_split.xlsx"
DEMO_TRACES_PARQUET = DEMO_DIR / "demo_traces.parquet"


def _must_exist(p: Path, label: str) -> Path:
    p = Path(p)
    if not p.exists():
        raise FileNotFoundError(f"{label} not found at: {p}")
    return p


# -------------------------
# Persistence: saved runs folder (demo)
# -------------------------
SAVED_RUNS_DIR = Path(os.environ.get("RUNS_DIR", str(APP_DIR / "saved_runs")))
SAVED_RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _now_run_id() -> str:
    return time.strftime("%Y-%m-%d_%H-%M-%S")


# -------------------------
# Session state (match app.py expectations)
# -------------------------
if "logs" not in st.session_state:
    st.session_state.logs = ""
if "outputs" not in st.session_state:
    st.session_state.outputs = None
if "loaded_manifest" not in st.session_state:
    st.session_state.loaded_manifest = None


def log(msg: str) -> None:
    st.session_state.logs += msg.rstrip() + "\n"


# -------------------------
# Load demo outs once
# -------------------------
def _load_demo_outputs():
    split_xlsx = _must_exist(DEMO_SPLIT_XLSX, "Demo Step 4 split workbook (split_xlsx)")
    traces_parquet = _must_exist(DEMO_TRACES_PARQUET, "Demo Step 4 traces parquet (traces_parquet)")

    # Use a simple object with attributes (matches outs.<attr> usage everywhere)
    return SimpleNamespace(
        merged_xlsx=None,
        stereo_xlsx=None,
        sites_xlsx=None,
        split_xlsx=split_xlsx,
        traces_parquet=traces_parquet,
    )



if st.session_state.outputs is None:
    try:
        st.session_state.outputs = _load_demo_outputs()
        st.session_state.loaded_manifest = "DEMO_DATASET"
        log("✅ Demo dataset loaded.")
    except Exception as e:
        st.error("Demo dataset could not be loaded. Check demo_data/ files.")
        st.exception(e)
        st.stop()


# -------------------------
# Sidebar (demo-mode version)
# -------------------------
with st.sidebar:
    st.header("Demo settings")
    st.info("Read-only demo. Pipeline execution is disabled.")

    st.write("Demo split workbook:")
    st.code(str(DEMO_SPLIT_XLSX))
    st.write("Demo traces parquet:")
    st.code(str(DEMO_TRACES_PARQUET))

    st.divider()
    st.header("Logs")
    st.code(st.session_state.logs or "(no logs yet)", language="text")

    st.divider()
    if st.button("Reset demo session"):
        st.session_state.logs = ""
        st.session_state.outputs = None
        st.session_state.loaded_manifest = None
        st.rerun()


# -------------------------
# Tabs: Pipeline vs Viewer vs Stats
# -------------------------
tab_info, tab_pipeline, tab_viewer, tab_stats = st.tabs(["Info", "Pipeline", "Viewer", "Stats"])

# -------------------------
# Info tab
# -------------------------
with tab_info:
    st.header("Proteomics Pipeline Overview")

    st.markdown(
        """
This application implements an end-to-end LC/MS proteomics analysis pipeline
designed to quantify stereoselective covalent labeling events and visualize
chromatographic evidence supporting site-level calls.

This tab provides a high-level overview of the pipeline logic, data flow,
and interpretation of outputs.
"""
    )

    st.divider()

    # -------------------------
    st.subheader("Pipeline Structure")

    st.markdown(
        """
The pipeline is organized into **four sequential stages**, each producing
intermediate outputs that feed into downstream analysis:

1. **Log2FC Compilation**
2. **Stereoselectivity Scoring + UniProt Annotation**
3. **Peptide-to-Site Mapping**
4. **Chromatographic Peak Splitting + Trace Extraction**

Each stage can be inspected independently once outputs are generated.
"""
    )

    st.divider()

    # -------------------------
    st.subheader("Step 1: Log2FC Compilation (Input CSVs)")

    st.markdown(
        """
**Purpose:**  
Aggregate replicate-level LC/MS quantification files into a unified
wide-format dataset containing Log2 fold-change values.

**Key concepts:**
- Supports both MS2 and MS3 quantification
- Automatically infers MS level and dynamic exclusion window (0s / 5s / 30s)
- Handles multiple injections per condition

**Primary output:**  
`merged_log2fc.xlsx`
"""
    )

    st.divider()

    # -------------------------
    st.subheader("Step 2: Stereoselectivity Analysis")

    st.markdown(
        """
**Purpose:**  
Compute site-level stereoselectivity scores and integrate protein annotations.

**Key concepts:**
- Window-aware scoring across available MS2/MS3 data
- Adaptive hit calling based on data completeness
- UniProt metadata enrichment

**Primary output:**  
`merged_log2fc_results.xlsx`
"""
    )

    st.divider()

    # -------------------------
    st.subheader("Step 3: Peptide Mapping")

    st.markdown(
        """
**Purpose:**  
Map quantified peptides to specific modification sites and protein positions.

**Key concepts:**
- Uses FragPipe peptide mapping outputs
- Resolves ambiguous peptide-to-site relationships
- Produces a site-centric view of the dataset

**Primary output:**  
`merged_log2fc_results_sites.xlsx`
"""
    )

    st.divider()

    # -------------------------
    st.subheader("Step 4: Chromatographic Peak Splitting")

    st.markdown(
        """
**Purpose:**  
Analyze Skyline chromatograms to detect peak splitting and extract
chromatographic traces for visualization.

**Key concepts:**
- Identifies single vs split peaks
- Computes quantitative splitting metrics
- Extracts full chromatographic traces into a columnar format

**Primary outputs:**
- Final split workbook (`*_split.xlsx`)
- Chromatographic traces (`chrom_traces.parquet`)
"""
    )

    st.divider()

    # -------------------------
    st.subheader("Viewer Tab")

    st.markdown(
        """
The **Viewer** tab enables interactive inspection of chromatographic evidence
supporting individual site calls.

**Features include:**
- Filtering by hit category and scoring metrics
- Interactive trace visualization
- Cross-navigation between related sites and conditions

This tab is intended for **manual validation and exploratory analysis**.
"""
    )

    st.divider()

    # -------------------------
    st.subheader("Stats Tab")

    st.markdown(
        """
The **Stats** tab provides summary-level views of the dataset, including:

- Hit counts and overlap summaries
- Distributions of stereoselectivity scores
- Comparisons across MS modes and windows

These views are designed to support high-level interpretation
and dataset quality assessment.
"""
    )

    st.divider()

    # -------------------------
    st.subheader("Interpreting Results")

    st.markdown(
        """
When interpreting results from this pipeline, consider:

- Consistency across MS modes and time windows
- Chromatographic support for site-level calls
- Potential confounding effects from peptide coverage or peak interference

Final conclusions should integrate **both quantitative scores and
chromatographic evidence**.
"""
    )

# -------------------------
# Pipeline tab (read-only UI mirror)
# -------------------------
with tab_pipeline:
    st.header("Pipeline (Demo / Read-only)")

    st.warning(
        "This tab is shown to demonstrate the wizard workflow, but **uploads and running the pipeline are disabled** "
        "in the demo. Use the Viewer/Stats tabs to explore the preloaded results."
    )

    st.subheader("Step 1: Upload CSVs (batch)")
    st.text_input(
        "Upload any number of LFC CSVs (filenames should include MS2/MS3 and ideally 0s/5s/30s)",
        value="(disabled in demo)",
        disabled=True,
    )

    st.subheader("Step 3: Upload peptide mapping files (batch)")
    st.text_input(
        "Upload peptide mapping inputs (combined_peptide_MS3.tsv, peptide_list_MS3.txt, combined_peptide_MS2.tsv, peptide_list_MS2.txt)",
        value="(disabled in demo)",
        disabled=True,
    )

    st.subheader("Step 4: Upload Skyline exports + peak boundaries (batch)")
    st.text_input(
        "Upload Skyline TSV exports + peak boundaries CSV reports",
        value="(disabled in demo)",
        disabled=True,
    )

    st.divider()
    st.button("Run pipeline", type="primary", disabled=True)

    # Outputs list (demo)
    outs = st.session_state.outputs
    if outs is not None:
        st.header("Outputs (Demo)")

        def dl(label: str, path: Optional[Path]):
            if not path:
                st.write(f"— **{label}**: (not included in demo)")
                return
            path = Path(path)
            if path.exists():
                st.write(f"✅ **{label}**: `{path.name}`")
                st.download_button(
                    label=f"Download {path.name}",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime="application/octet-stream",
                )
            else:
                st.write(f"❌ **{label}** missing: `{path}`")

        dl("Step 4 splitting workbook", getattr(outs, "split_xlsx", None))
        dl("Step 4 traces parquet", getattr(outs, "traces_parquet", None))


# -------------------------
# Viewer tab
# -------------------------
with tab_viewer:
    outs = st.session_state.outputs

    if st.session_state.loaded_manifest:
        st.caption("Loaded run: `DEMO_DATASET`")

    if outs is None:
        st.info("No dataset loaded (unexpected in demo).")
    else:
        if not getattr(outs, "split_xlsx", None) or not getattr(outs, "traces_parquet", None):
            st.error("Demo dataset is missing Step 4 outputs (split workbook + traces parquet).")
        else:
            st.header("Viewer")
            render_viewer(
                xlsx_path=outs.split_xlsx,
                traces_path=outs.traces_parquet,
                embedded=True,
            )


# -------------------------
# Stats tab
# -------------------------
with tab_stats:
    outs = st.session_state.outputs
    if outs is None:
        st.info("No dataset loaded (unexpected in demo).")
    else:
        st.header("Stats")
        render_stats(
            stereo_xlsx=None,
            split_xlsx=getattr(outs, "split_xlsx", None),
            embedded=True,
        )
