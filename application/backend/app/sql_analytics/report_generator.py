from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

import pandas as pd

from app.cleaning.config import config


class SQLReportGenerator:
    """Render SQL query results into plain-text business reports."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or config.SQL_INSIGHTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_category_report(
        self,
        title: str,
        results: Mapping[str, pd.DataFrame],
        file_name: str,
        summary_lines: Optional[Iterable[str]] = None,
    ) -> Path:
        path = self.output_dir / file_name
        lines = self._report_header(title)
        if summary_lines:
            lines.extend(summary_lines)
            lines.append("")

        for query_name, df in results.items():
            lines.append(query_name.replace("_", " ").title())
            lines.append("-" * 80)
            lines.extend(self._format_dataframe(df))
            lines.append("")

        path.write_text("\n".join(lines), encoding=config.ENCODING)
        return path

    def save_executive_report(
        self,
        kpi_results: Mapping[str, pd.DataFrame],
        analysis_results: Mapping[str, Mapping[str, pd.DataFrame]],
        recommendations: List[str],
    ) -> Path:
        path = self.output_dir / "executive_business_report.txt"
        lines = self._report_header("EXECUTIVE BUSINESS REPORT")

        lines.extend(["KPI SUMMARY", "-" * 80])
        lines.extend(self._format_metric_table(kpi_results))
        lines.append("")

        section_map = {
            "customer": "CUSTOMER INSIGHTS",
            "product": "PRODUCT INSIGHTS",
            "revenue": "REVENUE INSIGHTS",
            "referral": "REFERRAL INSIGHTS",
            "order": "ORDER INSIGHTS",
            "payment": "PAYMENT INSIGHTS",
            "trend": "TREND INSIGHTS",
        }
        for key, title in section_map.items():
            lines.extend([title, "-" * 80])
            lines.extend(self._section_highlights(analysis_results.get(key, {})))
            lines.append("")

        lines.extend(["STRATEGIC RECOMMENDATIONS", "-" * 80])
        lines.extend(f"{idx}. {item}" for idx, item in enumerate(recommendations, 1))
        lines.extend(["", "=" * 80, "END OF EXECUTIVE BUSINESS REPORT", "=" * 80])

        path.write_text("\n".join(lines), encoding=config.ENCODING)
        return path

    @staticmethod
    def _report_header(title: str) -> List[str]:
        return [
            "=" * 80,
            title,
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

    @staticmethod
    def _format_dataframe(df: pd.DataFrame, max_rows: int = 20) -> List[str]:
        if df.empty:
            return ["No rows returned."]
        return df.head(max_rows).to_string(index=False).splitlines()

    def _format_metric_table(self, results: Mapping[str, pd.DataFrame]) -> List[str]:
        lines: List[str] = []
        for name, df in results.items():
            if df.empty:
                continue
            value = df.iloc[0, 0]
            lines.append(f"{name.replace('_', ' ').title():<35} {value}")
        return lines or ["No KPI metrics available."]

    def _section_highlights(self, results: Mapping[str, pd.DataFrame]) -> List[str]:
        lines: List[str] = []
        for name, df in list(results.items())[:3]:
            lines.append(name.replace("_", " ").title())
            lines.extend(self._format_dataframe(df, max_rows=5))
            lines.append("")
        return lines or ["No insights available."]
