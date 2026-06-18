from typing import Dict

import pandas as pd

from app.sql_analytics.report_generator import SQLReportGenerator
from app.sql_analytics.sql_executor import SQLExecutor


class ProductAnalyzer:
    sql_file = "product_analysis.sql"
    report_file = "product_insights.txt"
    title = "SQL PRODUCT INSIGHTS"

    def __init__(self, executor: SQLExecutor, reporter: SQLReportGenerator):
        self.executor = executor
        self.reporter = reporter

    def run(self) -> Dict[str, pd.DataFrame]:
        results = self.executor.execute_file(self.sql_file)
        self.reporter.save_category_report(self.title, results, self.report_file)
        return results
