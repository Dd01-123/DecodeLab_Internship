from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from app.cleaning.config import config
from app.visualization.chart_manager import ChartManager


class BusinessCharts:
    """Generate revenue and customer visuals from the cleaned dataset."""

    def __init__(self, df: pd.DataFrame, chart_manager: Optional[ChartManager] = None):
        self.df = df.copy()
        self.chart_manager = chart_manager or ChartManager()

    def generate_revenue_charts(self) -> List[Path]:
        paths: List[Path] = []
        revenue_dir = self.chart_manager.directory("revenue")

        for column in config.CATEGORICAL_COLUMNS:
            if column not in self.df.columns or "TotalPrice" not in self.df.columns:
                continue
            grouped = (
                self.df.groupby(column, dropna=False)["TotalPrice"]
                .sum()
                .sort_values(ascending=False)
                .head(12)
                .reset_index(name="Revenue")
            )
            bar_path = self.chart_manager.bar_chart(
                grouped,
                column,
                "Revenue",
                f"Revenue by {column}",
                revenue_dir / f"revenue_by_{column}.png",
                horizontal=len(grouped) > 6,
                color="seagreen",
            )
            if bar_path:
                paths.append(bar_path)

            if column in {"Product", "PaymentMethod", "ReferralSource"}:
                pie_path = self.chart_manager.pie_chart(
                    grouped[column].astype(str),
                    grouped["Revenue"],
                    f"Revenue Share by {column}",
                    revenue_dir / f"revenue_share_by_{column}.png",
                )
                if pie_path:
                    paths.append(pie_path)
        return paths

    def generate_customer_charts(self) -> List[Path]:
        if "CustomerID" not in self.df.columns:
            return []

        paths: List[Path] = []
        customer_dir = self.chart_manager.directory("customers")

        customer_orders = (
            self.df.groupby("CustomerID")
            .agg(Orders=("OrderID", "nunique") if "OrderID" in self.df.columns else ("CustomerID", "size"))
            .sort_values("Orders", ascending=False)
            .head(15)
            .reset_index()
        )
        path = self.chart_manager.bar_chart(
            customer_orders,
            "CustomerID",
            "Orders",
            "Top Customers by Orders",
            customer_dir / "top_customers_by_orders.png",
            horizontal=True,
            color="slateblue",
        )
        if path:
            paths.append(path)

        if "TotalPrice" in self.df.columns:
            customer_revenue = (
                self.df.groupby("CustomerID")["TotalPrice"]
                .sum()
                .sort_values(ascending=False)
                .head(15)
                .reset_index(name="Revenue")
            )
            path = self.chart_manager.bar_chart(
                customer_revenue,
                "CustomerID",
                "Revenue",
                "Top Customers by Revenue",
                customer_dir / "top_customers_by_revenue.png",
                horizontal=True,
                color="darkorange",
            )
            if path:
                paths.append(path)

        return paths

    def generate_all(self) -> Dict[str, List[Path]]:
        return {
            "revenue": self.generate_revenue_charts(),
            "customers": self.generate_customer_charts(),
        }
