"""
Page 8: Data Management, Automation Status, and Pipeline Monitoring.
"""

import sys
from pathlib import Path

# Ensure repository root is on sys.path for Streamlit Community Cloud package resolution
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Data Management | Netflix Analytics", page_icon="⚙️", layout="wide")

from dashboard.components import (

    ApiClient,
    apply_netflix_theme,
    render_section_header
)

apply_netflix_theme()

st.markdown('<div class="netflix-brand-title">⚙️ Data Pipeline & Automation Management</div>', unsafe_allow_html=True)
st.markdown('<div class="netflix-brand-subtitle">Monitor scheduler operations, audit pipeline execution history, inspect source fingerprints, and trigger on-demand ETL refreshes.</div>', unsafe_allow_html=True)

client = ApiClient()

# System Status Overview
with st.spinner("Checking API, Database, and Scheduler Health..."):
    health_resp = client.get_health()
    status_resp = client.get_pipeline_status()
    auto_resp = client.get_automation_status()

h_data = health_resp.get("data", {}) if health_resp.get("success") else {}
p_data = status_resp.get("data", {}) if status_resp.get("success") else {}
a_data = auto_resp.get("data", {}) if auto_resp.get("success") else {}

col_h1, col_h2, col_h3 = st.columns(3)

with col_h1:
    api_status = "ONLINE" if health_resp.get("success") else "OFFLINE"
    status_color = "#46D369" if api_status == "ONLINE" else "#E50914"
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">FastAPI Backend</div>
            <div class="netflix-kpi-value" style="color: {status_color}; font-size:1.8rem;">{api_status}</div>
            <div class="netflix-kpi-subtext">Version: {h_data.get('version', '1.0.0')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_h2:
    db_status = h_data.get("database", "disconnected").upper()
    db_color = "#46D369" if db_status == "CONNECTED" else "#E50914"
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Database Connection</div>
            <div class="netflix-kpi-value" style="color: {db_color}; font-size:1.8rem;">{db_status}</div>
            <div class="netflix-kpi-subtext">Total Records: {h_data.get('database_record_count', 0):,}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_h3:
    sched_on = a_data.get("scheduler_running", False)
    sched_color = "#46D369" if sched_on else "#888888"
    sched_text = "ACTIVE" if sched_on else ("STANDBY" if a_data.get("scheduler_enabled") else "DISABLED")
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Background Scheduler</div>
            <div class="netflix-kpi-value" style="color: {sched_color}; font-size:1.8rem;">{sched_text}</div>
            <div class="netflix-kpi-subtext">Interval: {a_data.get('update_frequency_seconds', 3600)}s</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------------------------------------------------------
# A. AUTOMATION STATUS & SCHEDULE
# -----------------------------------------------------------------------------
render_section_header("A. Automation & Scheduled Refresh Status")

col_a1, col_a2, col_a3, col_a4 = st.columns(4)

with col_a1:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Scheduler Status</div>
            <div class="netflix-kpi-value" style="font-size:1.4rem;">{'RUNNING' if a_data.get('scheduler_running') else 'OFF'}</div>
            <div class="netflix-kpi-subtext">Enabled: {a_data.get('scheduler_enabled', False)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_a2:
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Refresh Frequency</div>
            <div class="netflix-kpi-value" style="font-size:1.4rem;">{a_data.get('update_frequency_seconds', 3600)}s</div>
            <div class="netflix-kpi-subtext">Every {a_data.get('update_frequency_seconds', 3600)//60} minutes</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_a3:
    next_run = a_data.get("next_scheduled_run") or "None scheduled"
    if "T" in next_run:
        next_run = next_run.replace("T", " ")[:19]
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Next Scheduled Run</div>
            <div class="netflix-kpi-value" style="font-size:1.1rem; margin-top:0.4rem;">{next_run}</div>
            <div class="netflix-kpi-subtext">Active interval trigger</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_a4:
    last_succ = a_data.get("last_successful_refresh")
    last_succ_time = (last_succ.get("completed_at") or "None yet") if last_succ else "None yet"
    if "T" in last_succ_time:
        last_succ_time = last_succ_time.replace("T", " ")[:19]
    st.markdown(
        f"""
        <div class="netflix-kpi-card">
            <div class="netflix-kpi-label">Last Successful Refresh</div>
            <div class="netflix-kpi-value" style="font-size:1.1rem; margin-top:0.4rem;">{last_succ_time}</div>
            <div class="netflix-kpi-subtext">Trigger: {last_succ.get('trigger_type') if last_succ else 'N/A'}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------------------------------------------------------
# B. SOURCE MONITORING & FINGERPRINT
# -----------------------------------------------------------------------------
render_section_header("B. Data Source Fingerprinting & Change Detection")

st.markdown(
    f"""
    <div style="background-color: #1F1F1F; border: 1px solid #2E2E2E; border-radius: 8px; padding: 1.2rem; font-size: 0.9rem;">
        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 0.6rem;">
            <div><strong style="color: #aaa;">Monitored Data Source:</strong></div>
            <div><code style="color: #fff;">{p_data.get('configured_data_source_path', 'data/netflix_titles.csv')}</code> ({p_data.get('configured_data_source_type', 'CSV').upper()})</div>
            <div><strong style="color: #aaa;">Configured Ingestion Mode:</strong></div>
            <div><code style="color: #fff;">{p_data.get('configured_update_mode', 'insert_new_only')}</code></div>
            <div><strong style="color: #aaa;">Change Detection Rule:</strong></div>
            <div><span style="color: #46D369;">SHA-256 Checksum + File Size + Row Count Comparison</span></div>
            <div><strong style="color: #aaa;">Last Ingestion Fingerprint:</strong></div>
            <div><code style="color: #aaa;">{(a_data.get('last_pipeline_run') or {}).get('source_fingerprint') or 'Initial baseline recorded'}</code></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# C. MANUAL PIPELINE REFRESH
# -----------------------------------------------------------------------------
render_section_header("C. On-Demand Pipeline Execution (Manual Override)")

col_mode, col_btn = st.columns([2, 1])

with col_mode:
    selected_mode = st.selectbox(
        "Ingestion Update Mode",
        options=["insert_new_only", "upsert"],
        help="'insert_new_only': Appends only new show_ids; skips existing.\n'upsert': Updates existing records and inserts new ones."
    )

with col_btn:
    st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
    trigger_refresh = st.button("🚀 Trigger Manual Refresh", width="stretch")

if trigger_refresh:
    with st.spinner(f"Running ETL pipeline in mode '{selected_mode}'..."):
        refresh_resp = client.refresh_pipeline(mode=selected_mode)

    if refresh_resp["success"]:
        rep = refresh_resp["data"]
        metrics = rep.get("incremental_metrics", {})
        status_code = rep.get("final_status", "SUCCESS")
        
        if status_code == "SKIPPED":
            st.warning(f"⏸️ Pipeline SKIPPED: {rep.get('message', 'Source unchanged')}")
        else:
            st.success(f"✅ Pipeline Execution {status_code} (Run ID: {rep.get('run_id')}) in {rep.get('duration_seconds')} seconds!")

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("Incoming Records", f"{metrics.get('incoming_records', 0):,}")
            st.metric("Inserted", f"{metrics.get('inserted', 0):,}")
        with m_col2:
            st.metric("Internal Duplicates", f"{metrics.get('internal_duplicates', 0):,}")
            st.metric("Updated", f"{metrics.get('updated', 0):,}")
        with m_col3:
            st.metric("New Records", f"{metrics.get('new_records', 0):,}")
            st.metric("Skipped", f"{metrics.get('skipped', 0):,}")
        with m_col4:
            st.metric("Existing in DB", f"{metrics.get('existing_records', 0):,}")
            st.metric("Total in DB Now", f"{rep.get('final_database_total', 0):,}")

        with st.expander("Inspect Raw Pipeline Execution Audit JSON"):
            st.json(rep)
    else:
        st.error(f"❌ **Pipeline Execution Failed**: {refresh_resp.get('error')}")

# -----------------------------------------------------------------------------
# D. PIPELINE EXECUTION AUDIT HISTORY
# -----------------------------------------------------------------------------
render_section_header("D. Pipeline Execution Audit History Ledger")

# Filter controls for history
col_hf1, col_hf2 = st.columns([2, 1])
with col_hf1:
    status_filter = st.selectbox(
        "Filter History by Status:",
        options=["All", "SUCCESS", "SKIPPED", "FAILED", "PARTIAL_SUCCESS", "RUNNING"]
    )
with col_hf2:
    history_limit = st.selectbox("Max records", options=[10, 25, 50], index=0)

history_resp = client.get_pipeline_history(limit=history_limit, status=status_filter)

if history_resp["success"]:
    h_result = history_resp["data"]
    total_runs = h_result.get("total", 0)
    runs = h_result.get("data", [])

    if not runs:
        st.info(f"No pipeline execution records found matching filter '{status_filter}'.")
    else:
        st.markdown(f"<span style='color: #888; font-size: 0.85rem;'>Displaying {len(runs)} of {total_runs} total execution records</span>", unsafe_allow_html=True)
        
        table_data = []
        for r in runs:
            # Map status badge colors
            st_color = {
                "SUCCESS": "🟢 SUCCESS",
                "PARTIAL_SUCCESS": "🟡 PARTIAL",
                "FAILED": "🔴 FAILED",
                "SKIPPED": "⚪ SKIPPED",
                "RUNNING": "🔵 RUNNING"
            }.get(r.get("status"), r.get("status"))

            started = r.get("started_at", "")
            if "T" in started:
                started = started.replace("T", " ")[:19]

            table_data.append({
                "Run ID": r.get("run_id"),
                "Status": st_color,
                "Trigger": r.get("trigger_type"),
                "Mode": r.get("update_mode"),
                "Started At": started,
                "Inserted": r.get("inserted", 0),
                "Updated": r.get("updated", 0),
                "Skipped": r.get("skipped", 0),
                "Duration (s)": f"{r.get('execution_duration', 0.0):.2f}" if r.get('execution_duration') is not None else "-",
                "Notes / Error": r.get("error_message") or "-"
            })

        df_history = pd.DataFrame(table_data)
        st.dataframe(df_history, width="stretch", hide_index=True)
else:
    st.error(f"Failed to load pipeline execution history: {history_resp.get('error')}")
