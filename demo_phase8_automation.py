"""
End-to-End Demonstration Script for Phase 8: Automation, Scheduling,
Source Change Detection, and Pipeline Monitoring.

Demonstrates:
  - Scenario A: First Run (Initial Fingerprint, ETL executes, PipelineRun recorded, SourceState saved)
  - Scenario B: Unchanged Source (Source fingerprint unchanged -> ETL Skipped)
  - Scenario C: Changed Source (New record appended -> Fingerprint changed -> ETL Ingestion runs)
  - Scenario D: Manual Refresh (API trigger_type=MANUAL override recorded)
  - Scenario E: Failure Safety (Missing/corrupted source -> FAILED status, DB intact, SourceState not updated)
"""

import os
import tempfile
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.database import Base
from database.models import PipelineRun, SourceState, NetflixContent
from automation.source_monitor import SourceMonitor
from automation.pipeline_monitor import PipelineMonitor
from automation.jobs import execute_pipeline_job
from automation.scheduler import get_scheduler_status

def run_demonstration():
    print("=" * 70)
    print("  PHASE 8: AUTOMATION, SCHEDULING & PIPELINE MONITORING DEMO")
    print("=" * 70)

    # Set up dedicated demo SQLite database
    db_file = "data/netflix_demo_phase8.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    DemoSession = sessionmaker(bind=engine)
    session = DemoSession()

    # Create a temporary CSV source
    tmp_source = "data/netflix_demo_source.csv"
    with open(tmp_source, "w", encoding="utf-8") as f:
        f.write("show_id,title,type,release_year,rating,duration,listed_in,description\n")
        f.write("s9001,Demo Pilot Movie,Movie,2021,PG-13,105 min,Dramas,A dramatic pilot film.\n")
        f.write("s9002,Demo Pilot Series,TV Show,2022,TV-MA,2 Seasons,TV Dramas,A gripping series.\n")

    try:
        # ---------------------------------------------------------------------
        # Scenario A: First Run (Initial Execution)
        # ---------------------------------------------------------------------
        print("\n[SCENARIO A] FIRST RUN (No Previous State)")
        print("-" * 50)
        fp_a = SourceMonitor.compute_source_fingerprint("csv", tmp_source)
        print(f"Source Fingerprint Computed: {fp_a['checksum'][:16]}... (Rows: {fp_a['row_count']})")
        
        changed, prev, reason = SourceMonitor.has_source_changed(session, fp_a)
        print(f"Change Detection: changed={changed} | Reason: {reason}")
        
        rep_a = execute_pipeline_job(
            trigger_type="SCHEDULED",
            mode="insert_new_only",
            source_type="csv",
            source_path=tmp_source,
            check_source_change=True,
            db=session
        )
        print(f"ETL Execution Status: {rep_a.get('final_status')} (Run ID: {rep_a.get('run_id')})")
        print(f"Metrics: Inserted={rep_a['incremental_metrics']['inserted']}, Duration={rep_a.get('duration_seconds')}s")

        # Verify DB records
        count_a = session.query(NetflixContent).count()
        run_count_a = session.query(PipelineRun).count()
        state_a = session.query(SourceState).first()
        print(f"Audit Ledger: {run_count_a} runs recorded | Titles in DB: {count_a} | SourceState stored: {state_a is not None}")

        # ---------------------------------------------------------------------
        # Scenario B: Unchanged Source
        # ---------------------------------------------------------------------
        print("\n[SCENARIO B] UNCHANGED SOURCE REFRESH")
        print("-" * 50)
        rep_b = execute_pipeline_job(
            trigger_type="SCHEDULED",
            mode="insert_new_only",
            source_type="csv",
            source_path=tmp_source,
            check_source_change=True,
            db=session
        )
        print(f"ETL Execution Status: {rep_b.get('final_status')} (Run ID: {rep_b.get('run_id')})")
        print(f"Notice: {rep_b.get('message')}")
        print(f"ETL Skipped: Inserted={rep_b['incremental_metrics']['inserted']}, Duration={rep_b.get('duration_seconds')}s")

        # ---------------------------------------------------------------------
        # Scenario C: Changed Source
        # ---------------------------------------------------------------------
        print("\n[SCENARIO C] SOURCE CHANGED (New Records Appended)")
        print("-" * 50)
        # Append new title
        with open(tmp_source, "a", encoding="utf-8") as f:
            f.write("s9003,Demo New Movie,Movie,2023,PG,90 min,Comedies,A hilarious new movie.\n")

        fp_c = SourceMonitor.compute_source_fingerprint("csv", tmp_source)
        print(f"New Fingerprint Computed: {fp_c['checksum'][:16]}... (Rows: {fp_c['row_count']})")

        rep_c = execute_pipeline_job(
            trigger_type="SCHEDULED",
            mode="insert_new_only",
            source_type="csv",
            source_path=tmp_source,
            check_source_change=True,
            db=session
        )
        print(f"ETL Execution Status: {rep_c.get('final_status')} (Run ID: {rep_c.get('run_id')})")
        print(f"Incremental Ingestion: Inserted={rep_c['incremental_metrics']['inserted']}, Skipped={rep_c['incremental_metrics']['skipped']}")
        print(f"Total Titles Now in DB: {session.query(NetflixContent).count()}")

        # ---------------------------------------------------------------------
        # Scenario D: Manual Refresh Trigger
        # ---------------------------------------------------------------------
        print("\n[SCENARIO D] MANUAL REFRESH TRIGGER (Override Change Check)")
        print("-" * 50)
        rep_d = execute_pipeline_job(
            trigger_type="MANUAL",
            mode="upsert",
            source_type="csv",
            source_path=tmp_source,
            check_source_change=False,
            db=session
        )
        print(f"Manual Refresh Status: {rep_d.get('final_status')} (Run ID: {rep_d.get('run_id')})")
        last_run = PipelineMonitor.get_last_run(session)
        print(f"Audit Ledger Trigger Type: {last_run.trigger_type} | Mode: {last_run.update_mode}")

        # ---------------------------------------------------------------------
        # Scenario E: Failure Handling
        # ---------------------------------------------------------------------
        print("\n[SCENARIO E] FAILURE RECOVERY (Missing Source File)")
        print("-" * 50)
        rep_e = execute_pipeline_job(
            trigger_type="SCHEDULED",
            mode="insert_new_only",
            source_type="csv",
            source_path="data/non_existent_file_error.csv",
            check_source_change=True,
            db=session
        )
        print(f"Failure Execution Status: {rep_e.get('final_status')}")
        print(f"Recorded Safe Error: {rep_e.get('error_message')}")
        
        # Verify DB remained intact and SourceState did not corrupt
        failed_run = PipelineMonitor.get_last_run(session)
        print(f"Audit Ledger Status: {failed_run.status} | DB Titles Count: {session.query(NetflixContent).count()}")

        # ---------------------------------------------------------------------
        # Audit Ledger Summary
        # ---------------------------------------------------------------------
        print("\n" + "=" * 70)
        print("  FINAL PIPELINE EXECUTION AUDIT HISTORY")
        print("=" * 70)
        total_runs, runs = PipelineMonitor.get_history(session)
        for r in runs:
            print(f"• Run [{r.run_id}]: Status={r.status:<8} | Trigger={r.trigger_type:<9} | Mode={r.update_mode:<15} | Inserted={r.inserted:<2} | Dur={r.execution_duration}s | Msg={r.error_message or 'OK'}")

        print("\n[SUCCESS] All 5 Demonstration Scenarios executed successfully!")

    finally:
        session.close()
        engine.dispose()
        if os.path.exists(tmp_source):
            os.remove(tmp_source)
        if os.path.exists(db_file):
            os.remove(db_file)

if __name__ == "__main__":
    run_demonstration()
