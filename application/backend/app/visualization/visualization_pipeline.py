import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from app.cleaning.config import config
from app.cleaning.data_loader import DataLoader
from app.visualization.business_charts import BusinessCharts
from app.visualization.categorical_charts import CategoricalCharts
from app.visualization.chart_manager import ChartManager
from app.visualization.correlation_charts import CorrelationCharts
from app.visualization.dashboard_generator import DashboardGenerator
from app.visualization.distribution_charts import DistributionCharts
from app.visualization.outlier_charts import OutlierCharts
from app.visualization.storytelling_engine import StorytellingEngine
from app.visualization.trend_charts import TrendCharts


logger = logging.getLogger(__name__)


class VisualizationPipelineError(Exception):
    """Raised when the visualization and storytelling phase fails."""


class VisualizationPipeline:
    """Phase 3 visualization, dashboard, and storytelling orchestrator."""

    def __init__(self, data_file_path: Optional[Path] = None):
        self.data_file_path = data_file_path or config.CLEANED_DATA_FILE
        self.chart_manager = ChartManager()
        self.df: Optional[pd.DataFrame] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def run(self) -> Dict[str, Any]:
        self.start_time = datetime.now()
        logger.info("=" * 80)
        logger.info("E-COMMERCE VISUALIZATION PIPELINE - EXECUTION STARTED")
        logger.info("=" * 80)

        try:
            self.df = self._load_data()
            generated_charts = {
                "distributions": DistributionCharts(self.df).generate(),
                "outliers": OutlierCharts(self.df).generate(),
                "correlations": CorrelationCharts(self.df).generate(),
                "categorical": CategoricalCharts(self.df).generate(),
                "trends": TrendCharts(self.df).generate(),
            }
            generated_charts.update(BusinessCharts(self.df, self.chart_manager).generate_all())

            dashboard_path = DashboardGenerator(self.df).generate()
            if dashboard_path:
                generated_charts["dashboards"] = [dashboard_path]

            storytelling = StorytellingEngine(self.df)
            visualization_summary = storytelling.generate_visualization_summary(generated_charts)
            storytelling_report = storytelling.generate_storytelling_report()
            executive_summary = storytelling.generate_executive_visual_summary()

            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            chart_count = sum(len(paths) for paths in generated_charts.values())
            logger.info("Visualization pipeline completed in %.2f seconds", duration)

            return {
                "status": "SUCCESS",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": duration,
                "charts_generated": chart_count,
                "chart_categories": {key: len(value) for key, value in generated_charts.items()},
                "reports_generated": [
                    str(visualization_summary),
                    str(storytelling_report),
                    str(executive_summary),
                ],
                "dashboard": str(dashboard_path) if dashboard_path else None,
            }
        except Exception as exc:
            self.end_time = datetime.now()
            logger.exception("Visualization pipeline failed")
            raise VisualizationPipelineError(str(exc)) from exc

    def _load_data(self) -> pd.DataFrame:
        df = DataLoader().load(self.data_file_path)
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        return df
