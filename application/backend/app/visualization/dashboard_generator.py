import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from app.cleaning.config import config


logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Create a static executive dashboard image from core business metrics."""

    def __init__(self, df: pd.DataFrame, output_dir: Optional[Path] = None):
        self.df = df.copy()
        self.output_dir = output_dir or (config.BASE_DIR / "visualizations" / "dashboards")

    def generate(self) -> Optional[Path]:
        if self.df.empty:
            return None

        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "executive_dashboard.png"

        fig, axes = plt.subplots(2, 2, figsize=(18, 12))
        fig.suptitle("Executive E-Commerce Visualization Dashboard", fontsize=18, fontweight="bold")

        self._plot_revenue_by_product(axes[0, 0])
        self._plot_order_status(axes[0, 1])
        self._plot_revenue_trend(axes[1, 0])
        self._plot_customer_revenue(axes[1, 1])

        fig.tight_layout(rect=[0, 0.02, 1, 0.95])
        plt.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        logger.info("Executive dashboard saved: %s", path)
        return path

    def _plot_revenue_by_product(self, ax) -> None:
        if {"Product", "TotalPrice"}.issubset(self.df.columns):
            data = (
                self.df.groupby("Product")["TotalPrice"]
                .sum()
                .sort_values(ascending=False)
                .head(8)
                .reset_index()
            )
            sns.barplot(data=data, x="TotalPrice", y="Product", ax=ax, color="seagreen")
            ax.set_title("Revenue by Product")
            ax.set_xlabel("Revenue")
        else:
            ax.text(0.5, 0.5, "Revenue by product unavailable", ha="center")

    def _plot_order_status(self, ax) -> None:
        if "OrderStatus" in self.df.columns:
            data = self.df["OrderStatus"].value_counts().reset_index()
            data.columns = ["OrderStatus", "Orders"]
            sns.barplot(data=data, x="OrderStatus", y="Orders", ax=ax, color="steelblue")
            ax.set_title("Order Status Distribution")
            ax.tick_params(axis="x", rotation=25)
        else:
            ax.text(0.5, 0.5, "Order status unavailable", ha="center")

    def _plot_revenue_trend(self, ax) -> None:
        if {"Date", "TotalPrice"}.issubset(self.df.columns):
            data = self.df.copy()
            data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
            data = (
                data.dropna(subset=["Date"])
                .groupby(pd.Grouper(key="Date", freq="ME"))["TotalPrice"]
                .sum()
                .reset_index()
            )
            sns.lineplot(data=data, x="Date", y="TotalPrice", marker="o", ax=ax, color="darkorange")
            ax.set_title("Monthly Revenue Trend")
            ax.tick_params(axis="x", rotation=30)
        else:
            ax.text(0.5, 0.5, "Revenue trend unavailable", ha="center")

    def _plot_customer_revenue(self, ax) -> None:
        if {"CustomerID", "TotalPrice"}.issubset(self.df.columns):
            data = (
                self.df.groupby("CustomerID")["TotalPrice"]
                .sum()
                .sort_values(ascending=False)
                .head(8)
                .reset_index()
            )
            sns.barplot(data=data, x="TotalPrice", y="CustomerID", ax=ax, color="slateblue")
            ax.set_title("Top Customers by Revenue")
            ax.set_xlabel("Revenue")
        else:
            ax.text(0.5, 0.5, "Customer revenue unavailable", ha="center")
