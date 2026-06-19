from pathlib import Path
from typing import List

import pandas as pd

from app.eda.distribution_analyzer import DistributionAnalyzer


class DistributionCharts:
    """Refresh numeric distribution charts using the existing EDA analyzer."""

    def __init__(self, df: pd.DataFrame):
        self.analyzer = DistributionAnalyzer(df)

    def generate(self) -> List[Path]:
        self.analyzer.analyze_all()
        return [
            self.analyzer.viz_dir / f"{column}_distribution.png"
            for column in self.analyzer.numeric_columns
        ]
