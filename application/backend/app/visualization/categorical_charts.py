from pathlib import Path
from typing import List

import pandas as pd

from app.eda.categorical_analyzer import CategoricalAnalyzer


class CategoricalCharts:
    """Refresh categorical bar and pie charts using the existing EDA analyzer."""

    def __init__(self, df: pd.DataFrame):
        self.analyzer = CategoricalAnalyzer(df)

    def generate(self) -> List[Path]:
        self.analyzer.analyze_all()
        paths: List[Path] = []
        for column, result in self.analyzer.categorical_results.items():
            paths.append(self.analyzer.viz_dir / f"{column}_bar_chart.png")
            if result.get("unique_categories", 99) <= 15:
                paths.append(self.analyzer.viz_dir / f"{column}_pie_chart.png")
        return paths
