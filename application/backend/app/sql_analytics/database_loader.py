import logging
import sqlite3
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from app.cleaning.config import config
from app.cleaning.data_loader import DataLoader


logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Load the cleaned e-commerce dataset into SQLite."""

    def __init__(
        self,
        cleaned_data_file: Optional[Path] = None,
        database_file: Optional[Path] = None,
        table_name: str = "ecommerce_orders",
    ):
        self.cleaned_data_file = cleaned_data_file or config.CLEANED_DATA_FILE
        self.database_file = database_file or config.ANALYTICS_DB_FILE
        self.table_name = table_name

    def load(self) -> Dict[str, object]:
        """Create the SQLite database and replace the analytics table."""
        logger.info("Loading cleaned dataset into SQLite: %s", self.cleaned_data_file)
        df = DataLoader().load(self.cleaned_data_file)
        df = self._prepare_dataframe(df)

        self.database_file.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_file) as connection:
            df.to_sql(self.table_name, connection, if_exists="replace", index=False)
            row_count = connection.execute(
                f'SELECT COUNT(*) FROM "{self.table_name}"'
            ).fetchone()[0]

        logger.info(
            "Loaded %s rows into %s.%s",
            row_count,
            self.database_file,
            self.table_name,
        )
        return {
            "database_file": str(self.database_file),
            "table_name": self.table_name,
            "rows_loaded": int(row_count),
            "columns_loaded": len(df.columns),
            "columns": list(df.columns),
        }

    @staticmethod
    def _prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        prepared = df.copy()
        if "Date" in prepared.columns:
            prepared["Date"] = pd.to_datetime(prepared["Date"], errors="coerce").dt.strftime(
                "%Y-%m-%d"
            )
        return prepared
