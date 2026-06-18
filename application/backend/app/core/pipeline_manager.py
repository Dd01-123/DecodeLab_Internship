import logging
from pathlib import Path
from typing import Iterable, List

from app.cleaning.config import config
from app.core.execution_context import ExecutionContext


logger = logging.getLogger(__name__)


class PipelineManager:
    """Utility operations for pipeline output discovery and bookkeeping."""

    REPORT_EXTENSIONS = {".txt", ".csv", ".json", ".xlsx", ".xls"}
    VISUALIZATION_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg", ".pdf"}

    def __init__(self, context: ExecutionContext):
        self.context = context

    def ensure_output_directories(self) -> None:
        for directory in (
            self.context.cleaned_data_file.parent,
            self.context.reports_dir,
            self.context.visualizations_dir,
            config.SQL_DIR,
            config.SQL_INSIGHTS_DIR,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def refresh_generated_outputs(self) -> None:
        self.context.generated_reports = self._collect_files(
            self.context.reports_dir,
            self.REPORT_EXTENSIONS,
        )
        self.context.generated_visualizations = self._collect_files(
            self.context.visualizations_dir,
            self.VISUALIZATION_EXTENSIONS,
        )

    @staticmethod
    def _collect_files(root: Path, extensions: Iterable[str]) -> List[Path]:
        if not root.exists():
            return []

        allowed = {ext.lower() for ext in extensions}
        return sorted(
            path for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in allowed
        )
