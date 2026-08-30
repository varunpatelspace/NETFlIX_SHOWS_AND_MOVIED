"""
SQLAlchemy ORM Data Models for Netflix Content.

Defines the database schema for storing validated, cleaned, and feature-engineered
Netflix movie and television show catalog records.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Date,
    DateTime,
    Text,
    func
)
from database.database import Base


class NetflixContent(Base):
    """
    Main entity table representing individual Netflix catalog titles.
    Stores raw metadata alongside derived temporal, duration, demographic,
    and multi-value features.
    """
    __tablename__ = "netflix_content"

    # Primary Identifier
    show_id = Column(String(50), primary_key=True, index=True, nullable=False)

    # Core Metadata
    type = Column(String(20), nullable=False, index=True)  # 'Movie' or 'TV Show'
    title = Column(String(500), nullable=False)
    director = Column(Text, nullable=True)
    cast = Column(Text, nullable=True)
    country = Column(Text, nullable=True)
    date_added = Column(Date, nullable=True)
    release_year = Column(Integer, nullable=True, index=True)
    rating = Column(String(50), nullable=True, index=True)
    duration = Column(String(50), nullable=True)
    listed_in = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    # Derived Temporal Features
    year_added = Column(Integer, nullable=True, index=True)
    month_added = Column(Integer, nullable=True)
    month_name_added = Column(String(20), nullable=True)
    day_added = Column(Integer, nullable=True)
    release_to_add_lag = Column(Float, nullable=True)

    # Derived Duration Features
    duration_min = Column(Float, nullable=True)  # Minutes for Movies
    seasons = Column(Integer, nullable=True)     # Season count for TV Shows
    movie_duration_tier = Column(String(50), nullable=True)

    # Derived Audience Demographic Classification
    age_group = Column(String(50), nullable=True, index=True)

    # Data Quality Tracking Flags
    has_director_info = Column(Boolean, default=True)
    has_cast_info = Column(Boolean, default=True)
    has_country_info = Column(Boolean, default=True)
    has_date_added = Column(Boolean, default=True)

    # Engineered Multi-Value Features
    primary_country = Column(String(100), nullable=True, index=True)
    country_count = Column(Integer, default=0)
    is_multi_country = Column(Boolean, default=False)
    primary_genre = Column(String(100), nullable=True, index=True)
    genre_count = Column(Integer, default=0)
    cast_count = Column(Integer, default=0)

    # Audit Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> dict:
        """Convert ORM model instance to a clean Python dictionary."""
        return {
            "show_id": self.show_id,
            "type": self.type,
            "title": self.title,
            "director": self.director,
            "cast": self.cast,
            "country": self.country,
            "date_added": str(self.date_added) if self.date_added else None,
            "release_year": self.release_year,
            "rating": self.rating,
            "duration": self.duration,
            "listed_in": self.listed_in,
            "description": self.description,
            "year_added": self.year_added,
            "month_added": self.month_added,
            "month_name_added": self.month_name_added,
            "day_added": self.day_added,
            "release_to_add_lag": self.release_to_add_lag,
            "duration_min": self.duration_min,
            "seasons": self.seasons,
            "movie_duration_tier": self.movie_duration_tier,
            "age_group": self.age_group,
            "has_director_info": self.has_director_info,
            "has_cast_info": self.has_cast_info,
            "has_country_info": self.has_country_info,
            "has_date_added": self.has_date_added,
            "primary_country": self.primary_country,
            "country_count": self.country_count,
            "is_multi_country": self.is_multi_country,
            "primary_genre": self.primary_genre,
            "genre_count": self.genre_count,
            "cast_count": self.cast_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<NetflixContent(show_id='{self.show_id}', title='{self.title}', type='{self.type}')>"


class PipelineRun(Base):
    """
    Persistent audit ledger of every executed ETL pipeline run.
    """
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(50), unique=True, nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(30), nullable=False, index=True)  # RUNNING, SUCCESS, PARTIAL_SUCCESS, FAILED, SKIPPED
    trigger_type = Column(String(30), nullable=False, index=True)  # MANUAL, SCHEDULED
    update_mode = Column(String(30), nullable=False)  # insert_new_only, upsert
    source_type = Column(String(30), nullable=True)
    source_identifier = Column(String(255), nullable=True)
    
    # Ingestion Metrics
    incoming_records = Column(Integer, default=0)
    internal_duplicates = Column(Integer, default=0)
    existing_records = Column(Integer, default=0)
    new_records = Column(Integer, default=0)
    inserted = Column(Integer, default=0)
    updated = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    
    execution_duration = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    source_fingerprint = Column(String(255), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "trigger_type": self.trigger_type,
            "update_mode": self.update_mode,
            "source_type": self.source_type,
            "source_identifier": self.source_identifier,
            "incoming_records": self.incoming_records,
            "internal_duplicates": self.internal_duplicates,
            "existing_records": self.existing_records,
            "new_records": self.new_records,
            "inserted": self.inserted,
            "updated": self.updated,
            "skipped": self.skipped,
            "failed": self.failed,
            "execution_duration": self.execution_duration,
            "error_message": self.error_message,
            "source_fingerprint": self.source_fingerprint,
        }

    def __repr__(self) -> str:
        return f"<PipelineRun(run_id='{self.run_id}', status='{self.status}', trigger='{self.trigger_type}')>"


class SourceState(Base):
    """
    Persistent tracker of external data source state for change detection.
    """
    __tablename__ = "source_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(30), nullable=False, index=True)
    source_identifier = Column(String(255), nullable=False, index=True)
    fingerprint = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    modified_time = Column(String(50), nullable=True)
    checksum = Column(String(100), nullable=True)
    row_count = Column(Integer, nullable=True)
    last_checked_at = Column(DateTime, nullable=False, default=func.now())
    last_successful_refresh = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_type": self.source_type,
            "source_identifier": self.source_identifier,
            "fingerprint": self.fingerprint,
            "file_size": self.file_size,
            "modified_time": self.modified_time,
            "checksum": self.checksum,
            "row_count": self.row_count,
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
            "last_successful_refresh": self.last_successful_refresh.isoformat() if self.last_successful_refresh else None,
        }

    def __repr__(self) -> str:
        return f"<SourceState(source='{self.source_identifier}', fingerprint='{self.fingerprint}')>"
