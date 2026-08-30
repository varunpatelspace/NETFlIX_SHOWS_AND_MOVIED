"""
Data Access Layer (Repository Pattern) for Netflix Content Database Operations.

Encapsulates all SQL and ORM queries, abstracting data persistence and retrieval
for the ETL pipeline, analytics engine, and FastAPI backend.
"""

from typing import List, Optional, Set, Dict, Any, Tuple
import pandas as pd
from sqlalchemy import func, distinct, desc, or_
from sqlalchemy.orm import Session

from database.models import NetflixContent


class NetflixRepository:
    """
    Repository providing query and persistence interfaces for NetflixContent entities.
    """

    def __init__(self, db: Session):
        self.db = db

    # -------------------------------------------------------------------------
    # Ingestion & Mutation Operations
    # -------------------------------------------------------------------------

    def insert_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        Insert a batch of dictionary records into the netflix_content table.
        
        Args:
            records: List of dictionaries matching NetflixContent fields.
            
        Returns:
            int: Count of successfully inserted rows.
        """
        if not records:
            return 0
        
        instances = []
        for r in records:
            # Handle date conversion if needed
            rec_copy = r.copy()
            if isinstance(rec_copy.get("date_added"), str) and rec_copy["date_added"]:
                try:
                    rec_copy["date_added"] = pd.to_datetime(rec_copy["date_added"]).date()
                except Exception:
                    rec_copy["date_added"] = None
            elif pd.isna(rec_copy.get("date_added")):
                rec_copy["date_added"] = None

            # Clean NaN to None for optional database fields
            for k, v in rec_copy.items():
                if pd.isna(v):
                    rec_copy[k] = None

            instances.append(NetflixContent(**rec_copy))

        try:
            self.db.bulk_save_objects(instances)
            self.db.commit()
            return len(instances)
        except Exception:
            self.db.rollback()
            raise

    def upsert_batch(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Insert new records and update existing records matched by show_id.
        Database-agnostic (works identically on SQLite and PostgreSQL).
        
        Returns:
            dict: {"inserted": count, "updated": count}
        """
        if not records:
            return {"inserted": 0, "updated": 0}

        try:
            existing_ids = self.get_existing_show_ids()
            to_insert = []
            updated_count = 0

            for r in records:
                show_id = str(r.get("show_id"))
                if show_id in existing_ids:
                    existing = self.get_by_show_id(show_id)
                    if existing:
                        for k, v in r.items():
                            val = None if pd.isna(v) else v
                            if k == "date_added" and isinstance(val, str) and val:
                                try:
                                    val = pd.to_datetime(val).date()
                                except Exception:
                                    val = None
                            if hasattr(existing, k) and k not in ("created_at", "show_id"):
                                setattr(existing, k, val)
                        updated_count += 1
                else:
                    to_insert.append(r)

            inserted_count = self.insert_batch(to_insert) if to_insert else 0
            self.db.commit()
            return {"inserted": inserted_count, "updated": updated_count}
        except Exception:
            self.db.rollback()
            raise

    def delete_all(self) -> int:
        """Delete all content records from the database table."""
        try:
            deleted = self.db.query(NetflixContent).delete()
            self.db.commit()
            return deleted
        except Exception:
            self.db.rollback()
            raise

    # -------------------------------------------------------------------------
    # Ingestion Status & Duplicate Detection Queries
    # -------------------------------------------------------------------------

    def get_existing_show_ids(self) -> Set[str]:
        """Retrieve the complete set of show_id primary keys currently in the database."""
        rows = self.db.query(NetflixContent.show_id).all()
        return {str(r[0]) for r in rows}

    def get_existing_title_signatures(self) -> Set[Tuple[str, str, Optional[int]]]:
        """
        Retrieve (title, type, release_year) tuples to prevent logical duplicates.
        """
        rows = self.db.query(
            NetflixContent.title, 
            NetflixContent.type, 
            NetflixContent.release_year
        ).all()
        return {(r[0].lower().strip(), r[1].lower().strip(), r[2]) for r in rows if r[0]}

    def get_total_count(self) -> int:
        """Get the total count of stored catalog titles."""
        return self.db.query(func.count(NetflixContent.show_id)).scalar() or 0

    def get_by_show_id(self, show_id: str) -> Optional[NetflixContent]:
        """Fetch a single record by its primary key."""
        return self.db.query(NetflixContent).filter(NetflixContent.show_id == str(show_id)).first()

    # -------------------------------------------------------------------------
    # Filtering & Analytics Data Retrieval
    # -------------------------------------------------------------------------

    def _build_filter_query(
        self,
        content_type: Optional[str] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        country: Optional[str] = None,
        genre: Optional[str] = None,
        rating: Optional[str] = None,
        age_group: Optional[str] = None,
        search: Optional[str] = None
    ):
        """Helper to construct filtered SQLAlchemy query based on dashboard filter criteria."""
        query = self.db.query(NetflixContent)

        if content_type and content_type.lower() != "all":
            query = query.filter(NetflixContent.type == content_type)
        if min_year is not None:
            query = query.filter(NetflixContent.release_year >= min_year)
        if max_year is not None:
            query = query.filter(NetflixContent.release_year <= max_year)
        if country and country.lower() != "all":
            query = query.filter(NetflixContent.country.ilike(f"%{country}%"))
        if genre and genre.lower() != "all":
            query = query.filter(NetflixContent.listed_in.ilike(f"%{genre}%"))
        if rating and rating.lower() != "all":
            query = query.filter(NetflixContent.rating == rating)
        if age_group and age_group.lower() != "all":
            query = query.filter(NetflixContent.age_group == age_group)
        if search:
            query = query.filter(
                or_(
                    NetflixContent.title.ilike(f"%{search}%"),
                    NetflixContent.director.ilike(f"%{search}%"),
                    NetflixContent.cast.ilike(f"%{search}%")
                )
            )

        return query

    def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
        content_type: Optional[str] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        country: Optional[str] = None,
        genre: Optional[str] = None,
        rating: Optional[str] = None,
        age_group: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[NetflixContent]:
        """Fetch filtered records as ORM model instances."""
        query = self._build_filter_query(content_type, min_year, max_year, country, genre, rating, age_group, search)
        query = query.order_by(desc(NetflixContent.release_year), NetflixContent.title)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    def get_dataframe(
        self,
        content_type: Optional[str] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        country: Optional[str] = None,
        genre: Optional[str] = None,
        rating: Optional[str] = None,
        age_group: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Query database and return results directly as a Pandas DataFrame,
        ideal for seamless analytics calculation and chart generation.
        """
        query = self._build_filter_query(content_type, min_year, max_year, country, genre, rating, age_group, search)
        if limit:
            query = query.limit(limit)

        # Use pd.read_sql for optimal C-speed data loading
        df = pd.read_sql(query.statement, self.db.bind)
        return df

    # -------------------------------------------------------------------------
    # Dimension & Distinct Values Retrieval
    # -------------------------------------------------------------------------

    def get_type_counts(self) -> Dict[str, int]:
        """Get counts grouped by 'Movie' and 'TV Show'."""
        rows = self.db.query(
            NetflixContent.type, 
            func.count(NetflixContent.show_id)
        ).group_by(NetflixContent.type).all()
        return {r[0]: r[1] for r in rows}

    def get_distinct_countries(self) -> List[str]:
        """Get sorted list of unique primary countries."""
        rows = self.db.query(
            distinct(NetflixContent.primary_country)
        ).filter(
            NetflixContent.primary_country.isnot(None),
            NetflixContent.primary_country != "Unknown Country"
        ).order_by(NetflixContent.primary_country).all()
        return [r[0] for r in rows if r[0]]

    def get_distinct_genres(self) -> List[str]:
        """Get sorted list of unique primary genres."""
        rows = self.db.query(
            distinct(NetflixContent.primary_genre)
        ).filter(
            NetflixContent.primary_genre.isnot(None),
            NetflixContent.primary_genre != "Unknown Genre"
        ).order_by(NetflixContent.primary_genre).all()
        return [r[0] for r in rows if r[0]]

    def get_min_max_years(self) -> Tuple[int, int]:
        """Get min and max release years available in the catalog."""
        row = self.db.query(
            func.min(NetflixContent.release_year),
            func.max(NetflixContent.release_year)
        ).first()
        min_yr = row[0] if row and row[0] else 1925
        max_yr = row[1] if row and row[1] else 2020
        return int(min_yr), int(max_yr)

    def get_latest_timestamp(self) -> Optional[str]:
        """Get the latest updated_at or created_at timestamp in ISO format."""
        latest = self.db.query(func.max(NetflixContent.updated_at)).scalar()
        return latest.isoformat() if latest else None
