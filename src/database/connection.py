"""
Database connection and session manager.
Supports PostgreSQL (production/docker) and SQLite (local zero-setup development).
Provides SQLAlchemy engine, session maker, and execution helpers.
"""

from typing import Optional
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from src.config import get_database_url, SQLITE_PATH, DEMO_SQLITE_PATH, DB_TYPE, DB_READONLY, is_database_available
from src.utils.logger import get_logger

logger = get_logger("db_connection")

class DatabaseManager:
    """Manages database connection lifecycle and query execution."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or get_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def _create_engine(self) -> Engine:
        """Creates an SQLAlchemy engine with graceful fallback if PostgreSQL or primary SQLite is not active."""
        try:
            if "postgresql" in self.db_url:
                # Test postgres connection with short timeout
                test_engine = create_engine(self.db_url, connect_args={"connect_timeout": 2})
                with test_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info(f"Connected to PostgreSQL database: {self.db_url.split('@')[-1]}")
                return test_engine
        except Exception as e:
            logger.warning(f"PostgreSQL not reachable ({e}). Falling back to local SQLite.")
            self.db_url = get_database_url()

        # If SQLite path does not exist, check demo database
        if "sqlite" in self.db_url:
            path_str = self.db_url.replace("sqlite:///", "")
            target_path = Path(path_str)
            if not target_path.exists() and DEMO_SQLITE_PATH.exists():
                logger.info(f"Primary SQLite file not found at {target_path}. Using verified demo database at {DEMO_SQLITE_PATH}")
                self.db_url = f"sqlite:///{DEMO_SQLITE_PATH.as_posix()}"

        engine = create_engine(
            self.db_url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in self.db_url else {}
        )
        logger.info(f"Initialized Database Engine: {self.db_url}")
        return engine

    def get_session(self) -> Session:
        """Returns a new SQLAlchemy ORM session."""
        return self.SessionLocal()

    def execute_query(self, query_str: str, params: Optional[dict] = None):
        """Executes raw SQL query and returns results as pandas DataFrame."""
        import pandas as pd
        with self.engine.connect() as conn:
            return pd.read_sql_query(text(query_str), conn, params=params)

    def execute_statement(self, sql_statement: str, params: Optional[dict] = None) -> None:
        """Executes a DDL or DML statement inside a transaction, respecting read-only guards."""
        if DB_READONLY:
            logger.warning("DB_READONLY is active: mutation statement blocked in demo environment.")
            return

        with self.engine.begin() as conn:
            conn.execute(text(sql_statement), params or {})

# Global singleton instance
db_manager = DatabaseManager()
