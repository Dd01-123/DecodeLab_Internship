import logging
from pathlib import Path
from typing import Iterable, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from app.cleaning.config import config


logger = logging.getLogger(__name__)

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["figure.figsize"] = (12, 7)
plt.rcParams["font.size"] = 10


class ChartManager:
    """Shared chart rendering utilities for the visualization phase."""

    def __init__(self, visualization_dir: Optional[Path] = None):
        self.visualization_dir = visualization_dir or (config.BASE_DIR / "visualizations")

    def directory(self, category: str) -> Path:
        path = self.visualization_dir / category
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_current(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(path, dpi=160, bbox_inches="tight", facecolor="white")
        plt.close()
        logger.info("Visualization saved: %s", path)
        return path

    def bar_chart(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        title: str,
        path: Path,
        horizontal: bool = False,
        color: str = "steelblue",
    ) -> Optional[Path]:
        if data.empty or x not in data.columns or y not in data.columns:
            return None

        fig, ax = plt.subplots(figsize=(12, max(6, min(12, len(data) * 0.5))))
        if horizontal:
            sns.barplot(data=data, x=y, y=x, ax=ax, color=color)
        else:
            sns.barplot(data=data, x=x, y=y, ax=ax, color=color)
            ax.tick_params(axis="x", rotation=35)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        return self.save_current(path)

    def pie_chart(
        self,
        labels: Iterable[str],
        values: Iterable[float],
        title: str,
        path: Path,
    ) -> Optional[Path]:
        values = list(values)
        labels = list(labels)
        if not values or sum(values) == 0:
            return None

        fig, ax = plt.subplots(figsize=(9, 8))
        ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
        ax.set_title(title, fontsize=14, fontweight="bold")
        fig.tight_layout()
        return self.save_current(path)

    def line_chart(
        self,
        data: pd.DataFrame,
        x: str,
        y: str,
        title: str,
        path: Path,
        color: str = "steelblue",
    ) -> Optional[Path]:
        if data.empty or x not in data.columns or y not in data.columns:
            return None

        fig, ax = plt.subplots(figsize=(13, 6))
        sns.lineplot(data=data, x=x, y=y, marker="o", ax=ax, color=color)
        ax.set_title(title, fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.25)
        ax.tick_params(axis="x", rotation=35)
        fig.tight_layout()
        return self.save_current(path)
