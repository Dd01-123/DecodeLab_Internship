from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from app.cleaning.config import config


class StorytellingEngine:
    """Convert visualization findings into executive business narratives."""

    def __init__(self, df: pd.DataFrame, output_dir: Optional[Path] = None):
        self.df = df.copy()
        self.output_dir = output_dir or config.VISUALIZATION_REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_storytelling_report(self) -> Path:
        findings = self.generate_findings()
        path = self.output_dir / "storytelling_report.txt"
        lines = self._header("DATA STORYTELLING REPORT")
        lines.extend(f"- {finding}" for finding in findings["narratives"])
        path.write_text("\n".join(lines), encoding=config.ENCODING)
        return path

    def generate_visualization_summary(self, generated_charts: Dict[str, List[Path]]) -> Path:
        path = self.output_dir / "visualization_summary.txt"
        lines = self._header("VISUALIZATION SUMMARY")
        for category, paths in generated_charts.items():
            lines.append(category.replace("_", " ").title())
            lines.append("-" * 80)
            lines.append(f"Charts generated: {len(paths)}")
            lines.extend(f"- {chart}" for chart in paths)
            lines.append("")
        path.write_text("\n".join(lines), encoding=config.ENCODING)
        return path

    def generate_executive_visual_summary(self) -> Path:
        findings = self.generate_findings()
        path = self.output_dir / "executive_visual_summary.txt"
        lines = self._header("EXECUTIVE VISUAL SUMMARY")
        lines.extend([
            "KEY CHART FINDINGS",
            "-" * 80,
            *[f"- {finding}" for finding in findings["narratives"][:6]],
            "",
            "BUSINESS RECOMMENDATIONS",
            "-" * 80,
            *[f"{idx}. {item}" for idx, item in enumerate(findings["recommendations"], 1)],
        ])
        path.write_text("\n".join(lines), encoding=config.ENCODING)
        return path

    def generate_findings(self) -> Dict[str, List[str]]:
        narratives: List[str] = []
        recommendations: List[str] = []
        total_revenue = self._total_revenue()

        if {"Product", "TotalPrice"}.issubset(self.df.columns) and total_revenue:
            product_revenue = self.df.groupby("Product")["TotalPrice"].sum().sort_values(ascending=False)
            top_product = product_revenue.index[0]
            top_share = product_revenue.iloc[0] / total_revenue * 100
            narratives.append(
                f"{top_product} is the primary product revenue driver, contributing {top_share:.2f}% of total revenue."
            )
            recommendations.append(
                f"Protect inventory and campaign visibility for {top_product}, the leading revenue product."
            )

        if {"ReferralSource", "TotalPrice"}.issubset(self.df.columns) and total_revenue:
            referral_revenue = self.df.groupby("ReferralSource")["TotalPrice"].sum().sort_values(ascending=False)
            top_referral = referral_revenue.index[0]
            narratives.append(
                f"{top_referral} is the strongest visualized acquisition channel by revenue."
            )
            recommendations.append(
                f"Use {top_referral} as the benchmark channel for budget allocation and campaign testing."
            )

        if "OrderStatus" in self.df.columns:
            status_pct = self.df["OrderStatus"].value_counts(normalize=True).mul(100)
            top_status = status_pct.index[0]
            delivered_pct = status_pct.get("Delivered", 0.0)
            cancelled_pct = status_pct.get("Cancelled", 0.0)
            narratives.append(
                f"{top_status} is the most common order status, while delivered orders represent {delivered_pct:.2f}% of activity."
            )
            narratives.append(
                f"Cancelled orders account for {cancelled_pct:.2f}% of orders, making cancellation monitoring a priority."
            )
            recommendations.append("Track delivered, cancelled, and returned orders as operational health KPIs.")

        if {"CustomerID", "TotalPrice"}.issubset(self.df.columns) and total_revenue:
            customer_revenue = self.df.groupby("CustomerID")["TotalPrice"].sum().sort_values(ascending=False)
            top_customer = customer_revenue.index[0]
            top_customer_share = customer_revenue.iloc[0] / total_revenue * 100
            narratives.append(
                f"Customer {top_customer} is the highest-value customer, contributing {top_customer_share:.2f}% of total revenue."
            )
            recommendations.append("Build targeted retention offers for the highest-value customer cohort.")

        if {"Date", "TotalPrice"}.issubset(self.df.columns):
            monthly = self.df.copy()
            monthly["Date"] = pd.to_datetime(monthly["Date"], errors="coerce")
            monthly = monthly.dropna(subset=["Date"])
            monthly_revenue = monthly.groupby(monthly["Date"].dt.to_period("M"))["TotalPrice"].sum()
            if not monthly_revenue.empty:
                best_month = str(monthly_revenue.idxmax())
                narratives.append(f"{best_month} is the strongest month in the revenue trend visualization.")
                recommendations.append("Review the campaign, product, and seasonality conditions behind the strongest revenue month.")

        return {
            "narratives": narratives or ["No visualization narratives could be generated from the available dataset."],
            "recommendations": recommendations or ["Review source data completeness before making business recommendations."],
        }

    def _total_revenue(self) -> float:
        if "TotalPrice" not in self.df.columns:
            return 0.0
        return float(self.df["TotalPrice"].sum())

    @staticmethod
    def _header(title: str) -> List[str]:
        return [
            "=" * 80,
            title,
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
