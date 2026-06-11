import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from app.cleaning.config import config


logger = logging.getLogger(__name__)

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)


class TrendAnalyzer:
    """
    Enterprise-grade trend analyzer for time-series data.
    
    Identifies date columns, aggregates data by time periods, and generates
    publication-quality time-series line charts with trend annotations.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with dataset.
        
        Args:
            df: DataFrame to analyze.
        """
        self.df = df.copy()
        self.date_columns = self._get_date_columns()
        self.trend_results: Dict[str, Dict[str, Any]] = {}
        self.viz_dir = config.BASE_DIR / 'visualizations' / 'trends'
        
    def _get_date_columns(self) -> List[str]:
        """
        Automatically identify date/datetime columns.
        
        Returns:
            List of date column names.
        """
        date_cols = []
        
        for col in self.df.columns:
            if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                date_cols.append(col)
                continue

            if col in config.DATE_COLUMNS:
                converted = pd.to_datetime(self.df[col], errors='coerce')
                if converted.notna().mean() >= 0.8:
                    date_cols.append(col)
                continue

            if pd.api.types.is_numeric_dtype(self.df[col]):
                continue

            normalized_name = col.lower()
            if not any(token in normalized_name for token in ('date', 'time', 'timestamp')):
                continue

            if self.df[col].nunique(dropna=True) > max(50, len(self.df) * 0.5):
                continue

            converted = pd.to_datetime(self.df[col], errors='coerce')
            if converted.notna().mean() >= 0.8:
                date_cols.append(col)
        
        logger.info(f"Identified {len(date_cols)} date columns: {date_cols}")
        return date_cols
    
    def _prepare_date_column(self, column_name: str) -> pd.Series:
        """
        Convert column to datetime and handle errors.
        
        Args:
            column_name: Column to convert.
            
        Returns:
            pd.Series: Datetime series.
        """
        if pd.api.types.is_datetime64_any_dtype(self.df[column_name]):
            return self.df[column_name]
        
        return pd.to_datetime(self.df[column_name], errors='coerce')
    
    def analyze_daily_trends(self, date_column: str, 
                             value_columns: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Analyze daily trends for specified value columns.
        
        Args:
            date_column: Date column to use for grouping.
            value_columns: Columns to aggregate.
            
        Returns:
            Dict with daily trend DataFrames.
        """
        dates = self._prepare_date_column(date_column)
        df_temp = self.df.copy()
        df_temp['_trend_date'] = dates
        df_temp['_trend_day'] = df_temp['_trend_date'].dt.date
        df_temp = df_temp.dropna(subset=['_trend_date'])
        
        daily_trends = {}
        
        for val_col in value_columns:
            if val_col not in df_temp.columns:
                continue
            
            daily = df_temp.groupby('_trend_day')[val_col].agg([
                ('count', 'count'),
                ('sum', 'sum'),
                ('mean', 'mean'),
                ('median', 'median'),
            ]).reset_index()
            
            daily.columns = ['Date', 'Count', 'Sum', 'Mean', 'Median']
            daily['Date'] = pd.to_datetime(daily['Date'])
            daily = daily.sort_values('Date')
            
            daily_trends[val_col] = daily
            logger.info(f"Daily trends calculated for '{val_col}': {len(daily)} days")
        
        return daily_trends
    
    def analyze_monthly_trends(self, date_column: str,
                              value_columns: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Analyze monthly trends for specified value columns.
        
        Args:
            date_column: Date column to use for grouping.
            value_columns: Columns to aggregate.
            
        Returns:
            Dict with monthly trend DataFrames.
        """
        dates = self._prepare_date_column(date_column)
        df_temp = self.df.copy()
        df_temp['_trend_date'] = dates
        df_temp['_trend_year'] = df_temp['_trend_date'].dt.year
        df_temp['_trend_month'] = df_temp['_trend_date'].dt.month
        df_temp = df_temp.dropna(subset=['_trend_date'])
        
        monthly_trends = {}
        
        for val_col in value_columns:
            if val_col not in df_temp.columns:
                continue
            
            monthly = df_temp.groupby(['_trend_year', '_trend_month'])[val_col].agg([
                ('count', 'count'),
                ('sum', 'sum'),
                ('mean', 'mean'),
            ]).reset_index()
            
            monthly.columns = ['Year', 'Month', 'Count', 'Sum', 'Mean']
            monthly['Period'] = pd.to_datetime(
                monthly['Year'].astype(str) + '-' + monthly['Month'].astype(str).str.zfill(2) + '-01'
            )
            monthly = monthly.sort_values(['Year', 'Month'])
            
            monthly_trends[val_col] = monthly
            logger.info(f"Monthly trends calculated for '{val_col}': {len(monthly)} months")
        
        return monthly_trends
    
    def analyze_weekly_trends(self, date_column: str,
                              value_columns: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Analyze weekly trends for specified value columns.
        
        Args:
            date_column: Date column to use for grouping.
            value_columns: Columns to aggregate.
            
        Returns:
            Dict with weekly trend DataFrames.
        """
        dates = self._prepare_date_column(date_column)
        df_temp = self.df.copy()
        df_temp['_trend_date'] = dates
        df_temp = df_temp.dropna(subset=['_trend_date'])
        df_temp['_trend_week'] = df_temp['_trend_date'].dt.isocalendar().week
        
        weekly_trends = {}
        
        for val_col in value_columns:
            if val_col not in df_temp.columns:
                continue
            
            weekly = df_temp.groupby('_trend_week')[val_col].agg([
                ('count', 'count'),
                ('sum', 'sum'),
                ('mean', 'mean'),
            ]).reset_index()
            
            weekly.columns = ['Week', 'Count', 'Sum', 'Mean']
            weekly = weekly.sort_values('Week')
            
            weekly_trends[val_col] = weekly
            logger.info(f"Weekly trends calculated for '{val_col}': {len(weekly)} weeks")
        
        return weekly_trends
    
    def generate_trend_chart(self, trend_data: pd.DataFrame,
                             title: str,
                             x_column: str,
                             y_column: str,
                             save_path: Path) -> Path:
        """
        Generate time-series line chart.
        
        Args:
            trend_data: DataFrame with trend data.
            title: Chart title.
            x_column: X-axis column name.
            y_column: Y-axis column name.
            save_path: Path to save figure.
            
        Returns:
            Path to saved figure.
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Plot line
        ax.plot(trend_data[x_column], trend_data[y_column], 
               marker='o', linewidth=2, markersize=4, color='steelblue')
        
        # Add trend line
        x_numeric = range(len(trend_data))
        z = np.polyfit(x_numeric, trend_data[y_column], 1)
        p = np.poly1d(z)
        ax.plot(trend_data[x_column], p(x_numeric), 
               "r--", alpha=0.7, linewidth=2, label=f'Trend (slope: {z[0]:.4f})')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_column, fontsize=11)
        ax.set_ylabel(y_column, fontsize=11)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels if needed
        if len(trend_data) > 10:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        logger.info(f"Trend chart saved: {save_path}")
        return save_path
    
    def analyze_all(self) -> Dict[str, Any]:
        """
        Run complete trend analysis.
        
        Returns:
            Dict with all trend analysis results.
        """
        logger.info("Starting trend analysis...")
        
        if not self.date_columns:
            logger.warning("No date columns found, skipping trend analysis")
            return {}
        
        date_col = self.date_columns[0]  # Use first date column
        
        # Identify numeric columns for trend analysis
        value_cols = [col for col in self.df.select_dtypes(include=[np.number]).columns 
                     if col != date_col]
        
        # Analyze trends
        daily = self.analyze_daily_trends(date_col, value_cols)
        monthly = self.analyze_monthly_trends(date_col, value_cols)
        weekly = self.analyze_weekly_trends(date_col, value_cols)
        
        # Generate visualizations
        for val_col, trend_df in daily.items():
            if len(trend_df) > 0:
                self.generate_trend_chart(
                    trend_df, 
                    f'Daily Trend: {val_col}',
                    'Date', 'Sum',
                    self.viz_dir / f'daily_{val_col}_trend.png'
                )
                self.generate_trend_chart(
                    trend_df,
                    f'Daily Order Count',
                    'Date', 'Count',
                    self.viz_dir / f'daily_count_trend.png'
                )
        
        for val_col, trend_df in monthly.items():
            if len(trend_df) > 0:
                self.generate_trend_chart(
                    trend_df,
                    f'Monthly Trend: {val_col}',
                    'Period', 'Sum',
                    self.viz_dir / f'monthly_{val_col}_trend.png'
                )
        
        self.trend_results = {
            'date_column': date_col,
            'value_columns': value_cols,
            'daily_trends': daily,
            'monthly_trends': monthly,
            'weekly_trends': weekly,
        }
        
        logger.info("Trend analysis complete")
        return self.trend_results.copy()
    
    def get_results(self) -> Dict[str, Any]:
        """Get trend analysis results."""
        if not self.trend_results:
            self.analyze_all()
        return self.trend_results.copy()
