from pathlib import Path
from typing import List

import pandas as pd

from app.eda.trend_analyzer import TrendAnalyzer


class TrendCharts:
    """Refresh time-series charts using the existing EDA trend analyzer."""

    def __init__(self, df: pd.DataFrame):
        self.analyzer = TrendAnalyzer(df)

    def generate(self) -> List[Path]:
        results = self.analyzer.analyze_all()
        paths: List[Path] = []
        for value_column in results.get("daily_trends", {}):
            paths.append(self.analyzer.viz_dir / f"daily_{value_column}_trend.png")
        for value_column in results.get("monthly_trends", {}):
            paths.append(self.analyzer.viz_dir / f"monthly_{value_column}_trend.png")
        if results.get("daily_trends"):
            paths.append(self.analyzer.viz_dir / "daily_count_trend.png")
        return paths
