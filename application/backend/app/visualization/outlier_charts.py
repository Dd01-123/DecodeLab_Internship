from pathlib import Path
from typing import List

import pandas as pd

from app.eda.outlier_detector import OutlierDetector


class OutlierCharts:
    """Refresh numeric outlier charts using the existing EDA detector."""

    def __init__(self, df: pd.DataFrame):
        self.detector = OutlierDetector(df)

    def generate(self) -> List[Path]:
        self.detector.analyze_all()
        return [
            self.detector.viz_dir / f"{column}_outliers.png"
            for column in self.detector.numeric_columns
        ]
