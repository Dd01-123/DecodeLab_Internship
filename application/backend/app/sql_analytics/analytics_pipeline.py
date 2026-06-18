import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from app.cleaning.config import config
from app.sql_analytics.customer_analysis import CustomerAnalyzer
from app.sql_analytics.database_loader import DatabaseLoader
from app.sql_analytics.kpi_analyzer import KPIAnalyzer
from app.sql_analytics.order_analysis import OrderAnalyzer
from app.sql_analytics.payment_analysis import PaymentAnalyzer
from app.sql_analytics.product_analysis import ProductAnalyzer
from app.sql_analytics.referral_analysis import ReferralAnalyzer
from app.sql_analytics.report_generator import SQLReportGenerator
from app.sql_analytics.revenue_analysis import RevenueAnalyzer
from app.sql_analytics.sql_executor import SQLExecutor
from app.sql_analytics.trend_analysis import TrendAnalyzer


logger = logging.getLogger(__name__)


class SQLAnalyticsPipelineError(Exception):
    """Raised when the SQL analytics phase fails."""


class SQLAnalyticsPipeline:
    """Phase 3 SQL analytics and executive reporting orchestrator."""

    def __init__(
        self,
        cleaned_data_file: Optional[Path] = None,
        database_file: Optional[Path] = None,
    ):
        self.cleaned_data_file = cleaned_data_file or config.CLEANED_DATA_FILE
        self.database_file = database_file or config.ANALYTICS_DB_FILE
        self.loader = DatabaseLoader(self.cleaned_data_file, self.database_file)
        self.executor = SQLExecutor(self.database_file)
        self.reporter = SQLReportGenerator()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results: Dict[str, Any] = {}

    def run(self) -> Dict[str, Any]:
        self.start_time = datetime.now()
        logger.info("=" * 80)
        logger.info("E-COMMERCE SQL ANALYTICS PIPELINE - EXECUTION STARTED")
        logger.info("=" * 80)

        try:
            load_results = self.loader.load()
            analyses = {
                "kpi": KPIAnalyzer(self.executor, self.reporter).run(),
                "customer": CustomerAnalyzer(self.executor, self.reporter).run(),
                "product": ProductAnalyzer(self.executor, self.reporter).run(),
                "revenue": RevenueAnalyzer(self.executor, self.reporter).run(),
                "order": OrderAnalyzer(self.executor, self.reporter).run(),
                "payment": PaymentAnalyzer(self.executor, self.reporter).run(),
                "referral": ReferralAnalyzer(self.executor, self.reporter).run(),
                "trend": TrendAnalyzer(self.executor, self.reporter).run(),
            }
            recommendations = self._generate_recommendations(analyses)
            executive_report = self.reporter.save_executive_report(
                analyses["kpi"],
                analyses,
                recommendations,
            )

            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            self.results = {
                "status": "SUCCESS",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": duration,
                "database_file": str(self.database_file),
                "rows_loaded": load_results["rows_loaded"],
                "columns_loaded": load_results["columns_loaded"],
                "reports_dir": str(config.SQL_INSIGHTS_DIR),
                "executive_report": str(executive_report),
                "advanced_business_answers": self._answer_business_questions(analyses),
                "recommendations": recommendations,
            }
            logger.info("SQL analytics pipeline completed in %.2f seconds", duration)
            return self.results
        except Exception as exc:
            self.end_time = datetime.now()
            logger.exception("SQL analytics pipeline failed")
            raise SQLAnalyticsPipelineError(str(exc)) from exc

    def _answer_business_questions(
        self,
        analyses: Dict[str, Dict[str, pd.DataFrame]],
    ) -> Dict[str, str]:
        product = analyses["product"]
        customer = analyses["customer"]
        referral = analyses["referral"]
        payment = analyses["payment"]
        order = analyses["order"]
        trend = analyses["trend"]

        return {
            "highest_revenue_products": self._first_value(product, "highest_revenue_products", "Product"),
            "highest_revenue_customers": self._first_value(customer, "top_customers_by_revenue", "CustomerID"),
            "top_sales_referral_source": self._first_value(referral, "top_referral_sources", "ReferralSource"),
            "preferred_payment_method": self._first_value(payment, "most_used_payment_method", "PaymentMethod"),
            "delivered_order_percentage": self._first_value(order, "delivered_orders", "percentage"),
            "cancelled_order_percentage": self._first_value(order, "cancelled_orders", "percentage"),
            "monthly_revenue_trends": self._first_value(trend, "monthly_revenue", "month"),
            "products_to_promote": self._first_value(product, "lowest_revenue_products", "Product"),
            "high_volume_low_revenue_products": self._first_value(
                product, "high_volume_low_revenue_products", "Product"
            ),
            "high_revenue_low_volume_products": self._first_value(
                product, "high_revenue_low_volume_products", "Product"
            ),
        }

    def _generate_recommendations(self, analyses: Dict[str, Dict[str, pd.DataFrame]]) -> list[str]:
        answers = self._answer_business_questions(analyses)
        return [
            f"Prioritize inventory and campaigns for top revenue products such as {answers['highest_revenue_products']}.",
            f"Build retention offers around high-value customers such as {answers['highest_revenue_customers']}.",
            f"Allocate more acquisition budget to the strongest referral source: {answers['top_sales_referral_source']}.",
            f"Keep checkout friction low for the preferred payment method: {answers['preferred_payment_method']}.",
            f"Promote low-revenue products selectively, starting with {answers['products_to_promote']}, after checking margin and stock position.",
            f"Review pricing and bundling for high-volume, low-revenue products such as {answers['high_volume_low_revenue_products']}.",
        ]

    @staticmethod
    def _first_value(
        analyses: Dict[str, pd.DataFrame],
        query_name: str,
        column_name: str,
    ) -> str:
        df = analyses.get(query_name)
        if df is None or df.empty or column_name not in df.columns:
            return "N/A"
        value = df.iloc[0][column_name]
        if isinstance(value, float):
            return f"{value:,.2f}"
        return str(value)
