"""
Data Source Change Detection and Fingerprinting Module.

Inspects configured data sources (CSV files or API endpoints) to detect changes
via file size, modification timestamps, row counts, and cryptographic checksums (SHA-256).
"""

import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func

from config.settings import DATA_SOURCE_TYPE, DATA_SOURCE_PATH
from database.models import SourceState


class SourceMonitor:
    """
    Inspects and fingerprints data sources to support conditional ETL execution.
    """

    @staticmethod
    def compute_source_fingerprint(
        source_type: Optional[str] = None,
        source_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a cryptographic and operational fingerprint for the configured data source.
        
        Args:
            source_type: 'csv' or 'api'
            source_path: File path or API URL
            
        Returns:
            Dict[str, Any]: Comprehensive source state metadata.
        """
        stype = (source_type or DATA_SOURCE_TYPE).lower()
        spath = source_path or DATA_SOURCE_PATH

        if stype == "csv":
            path_obj = Path(spath)
            if not path_obj.exists():
                return {
                    "exists": False,
                    "source_type": "csv",
                    "source_identifier": str(path_obj),
                    "error": f"CSV source file '{spath}' not found."
                }

            stat = path_obj.stat()
            file_size = stat.st_size
            mod_time = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

            # Compute SHA-256 hash in streaming 64KB blocks
            hasher = hashlib.sha256()
            line_count = 0
            with open(path_obj, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
                    line_count += chunk.count(b"\n")
            
            checksum = hasher.hexdigest()
            # Row count excluding header
            row_count = max(0, line_count - 1)

            return {
                "exists": True,
                "source_type": "csv",
                "source_identifier": str(path_obj.resolve()),
                "file_size": file_size,
                "modified_time": mod_time,
                "checksum": checksum,
                "row_count": row_count,
                "fingerprint": checksum
            }
        else:
            # API or generic data source
            identifier = str(spath)
            hasher = hashlib.sha256(identifier.encode("utf-8"))
            checksum = hasher.hexdigest()
            return {
                "exists": True,
                "source_type": stype,
                "source_identifier": identifier,
                "file_size": None,
                "modified_time": datetime.now(timezone.utc).isoformat(),
                "checksum": checksum,
                "row_count": None,
                "fingerprint": checksum
            }

    @classmethod
    def has_source_changed(
        cls,
        db: Session,
        current_fingerprint: Dict[str, Any]
    ) -> Tuple[bool, Optional[SourceState], str]:
        """
        Compare current fingerprint against the last persisted successful source state.
        
        Args:
            db: SQLAlchemy session
            current_fingerprint: Latest generated fingerprint dictionary
            
        Returns:
            Tuple[bool, Optional[SourceState], str]: (changed, previous_state, reason)
        """
        if not current_fingerprint.get("exists", False):
            return False, None, current_fingerprint.get("error", "Source unavailable")

        source_type = current_fingerprint["source_type"]
        source_id = current_fingerprint["source_identifier"]

        prev_state = db.query(SourceState).filter(
            SourceState.source_type == source_type,
            SourceState.source_identifier == source_id
        ).order_by(SourceState.id.desc()).first()

        if prev_state is None:
            return True, None, "Initial execution: No prior source state recorded"

        # Compare checksum and file size
        same_checksum = (prev_state.checksum == current_fingerprint["checksum"])
        same_size = (prev_state.file_size == current_fingerprint.get("file_size"))

        if same_checksum and same_size:
            return False, prev_state, "Source unchanged since previous successful refresh"

        return (
            True,
            prev_state,
            f"Source changed: checksum {prev_state.checksum[:8]} -> {current_fingerprint['checksum'][:8]}"
        )

    @classmethod
    def record_successful_source_state(
        cls,
        db: Session,
        fingerprint: Dict[str, Any]
    ) -> SourceState:
        """
        Persist source fingerprint in database following a successful ETL run.
        """
        source_type = fingerprint["source_type"]
        source_id = fingerprint["source_identifier"]
        now = datetime.now(timezone.utc)

        state = db.query(SourceState).filter(
            SourceState.source_type == source_type,
            SourceState.source_identifier == source_id
        ).first()

        if state is None:
            state = SourceState(
                source_type=source_type,
                source_identifier=source_id,
                fingerprint=fingerprint["fingerprint"],
                file_size=fingerprint.get("file_size"),
                modified_time=fingerprint.get("modified_time"),
                checksum=fingerprint.get("checksum"),
                row_count=fingerprint.get("row_count"),
                last_checked_at=now,
                last_successful_refresh=now
            )
            db.add(state)
        else:
            state.fingerprint = fingerprint["fingerprint"]
            state.file_size = fingerprint.get("file_size")
            state.modified_time = fingerprint.get("modified_time")
            state.checksum = fingerprint.get("checksum")
            state.row_count = fingerprint.get("row_count")
            state.last_checked_at = now
            state.last_successful_refresh = now

        db.commit()
        db.refresh(state)
        return state
