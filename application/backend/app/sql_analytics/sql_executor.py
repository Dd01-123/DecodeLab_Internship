import logging
import re
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd

from app.cleaning.config import config


logger = logging.getLogger(__name__)


class SQLExecutor:
    """Execute named SQL queries from reusable query library files."""

    QUERY_PATTERN = re.compile(
        r"--\s*name:\s*(?P<name>[A-Za-z0-9_]+)\s*\n(?P<sql>.*?)(?=\n--\s*name:|\Z)",
        re.DOTALL,
    )

    def __init__(
        self,
        database_file: Optional[Path] = None,
        sql_dir: Optional[Path] = None,
    ):
        self.database_file = database_file or config.ANALYTICS_DB_FILE
        self.sql_dir = sql_dir or config.SQL_DIR

    def execute_file(self, file_name: str) -> Dict[str, pd.DataFrame]:
        sql_path = self.sql_dir / file_name
        queries = self.load_queries(sql_path)
        return self.execute_queries(queries)

    def load_queries(self, sql_path: Path) -> Dict[str, str]:
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {sql_path}")

        content = sql_path.read_text(encoding=config.ENCODING)
        queries = {
            match.group("name"): match.group("sql").strip().rstrip(";")
            for match in self.QUERY_PATTERN.finditer(content)
        }
        if not queries:
            raise ValueError(f"No named SQL queries found in {sql_path}")
        return queries

    def execute_queries(self, queries: Dict[str, str]) -> Dict[str, pd.DataFrame]:
        with sqlite3.connect(self.database_file) as connection:
            return {
                name: pd.read_sql_query(sql, connection)
                for name, sql in queries.items()
            }

    def execute_scalar_query(self, sql: str):
        with sqlite3.connect(self.database_file) as connection:
            row = connection.execute(sql).fetchone()
        return row[0] if row else None

    def execute_many_files(self, file_names: Iterable[str]) -> Dict[str, Dict[str, pd.DataFrame]]:
        return {file_name: self.execute_file(file_name) for file_name in file_names}
