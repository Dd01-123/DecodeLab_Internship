from pathlib import Path
from typing import List

import pandas as pd

from app.eda.correlation_analyzer import CorrelationAnalyzer


class CorrelationCharts:
    """Refresh correlation heatmaps using the existing EDA analyzer."""

    def __init__(self, df: pd.DataFrame):
        self.analyzer = CorrelationAnalyzer(df)

    def generate(self) -> List[Path]:
        self.analyzer.analyze_all()
        return [
            self.analyzer.viz_dir / "pearson_correlation_heatmap.png",
            self.analyzer.viz_dir / "spearman_correlation_heatmap.png",
        ]
