from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionContext:
    """Runtime state shared across analytics pipeline phases."""

    raw_data_file: Path
    cleaned_data_file: Path
    reports_dir: Path
    visualizations_dir: Path
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    cleaning_results: Dict[str, Any] = field(default_factory=dict)
    eda_results: Dict[str, Any] = field(default_factory=dict)
    generated_reports: List[Path] = field(default_factory=list)
    generated_visualizations: List[Path] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def finish(self) -> None:
        self.end_time = datetime.now()

    @property
    def duration_seconds(self) -> float:
        end_time = self.end_time or datetime.now()
        return (end_time - self.start_time).total_seconds()
