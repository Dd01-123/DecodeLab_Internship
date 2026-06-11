import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

from .config import config


logger = logging.getLogger(__name__)


class DataQualityReporter:
    """
    Enterprise-grade data quality reporter.
    
    Generates comprehensive profiling reports and cleaning summaries
    with detailed before/after comparisons.
    """
    
    def __init__(self):
        """Initialize the reporter."""
        self.quality_metrics: Dict[str, Any] = {}
        self.cleaning_metrics: Dict[str, Any] = {}
        
    def generate_dataset_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate basic dataset overview metrics.
        
        Args:
            df: DataFrame to analyze.
            
        Returns:
            Dict[str, Any]: Overview metrics dictionary.
        """
        overview = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'column_names': list(df.columns),
            'memory_usage_mb': round(df.memory_usage(deep=True).sum() / (1024 ** 2), 4),
            'memory_usage_bytes': int(df.memory_usage(deep=True).sum()),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'timestamp': datetime.now().isoformat(),
        }
        logger.debug(f"Generated dataset overview: {overview['total_rows']} rows, {overview['total_columns']} columns")
        return overview
    
    def analyze_missing_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive missing value analysis.
        
        Detects NaN, null, blank strings, whitespace-only values,
        and other missing indicators defined in config.
        
        Args:
            df: DataFrame to analyze.
            
        Returns:
            Dict[str, Any]: Missing value analysis results.
        """
        missing_analysis = {
            'total_missing_cells': 0,
            'total_cells': df.shape[0] * df.shape[1],
            'overall_missing_percentage': 0.0,
            'per_column': {},
            'columns_with_missing': [],
            'columns_high_missing': [],  # > 50% missing
        }
        
        for col in df.columns:
            # Count standard NaN/Null
            nan_count = df[col].isna().sum()
            
            # Count string-based missing indicators (only for object columns)
            string_missing_count = 0
            if df[col].dtype == 'object':
                string_missing = df[col].astype(str).str.strip().str.lower().isin(
                    [indicator.lower() for indicator in config.MISSING_INDICATORS]
                )
                string_missing_count = string_missing.sum()
                
                # Also count empty/whitespace-only strings
                empty_or_whitespace = df[col].astype(str).str.strip().eq('')
                empty_count = empty_or_whitespace.sum()
                
                # Avoid double-counting
                string_missing_count = max(string_missing_count, empty_count)
            
            total_missing = int(nan_count + string_missing_count)
            missing_percentage = round((total_missing / len(df)) * 100, 2) if len(df) > 0 else 0.0
            
            missing_analysis['per_column'][col] = {
                'missing_count': total_missing,
                'missing_percentage': missing_percentage,
                'nan_count': int(nan_count),
                'string_missing_count': int(string_missing_count),
            }
            
            missing_analysis['total_missing_cells'] += total_missing
            
            if total_missing > 0:
                missing_analysis['columns_with_missing'].append(col)
            
            if missing_percentage > config.MAX_MISSING_PERCENTAGE:
                missing_analysis['columns_high_missing'].append(col)
        
        missing_analysis['overall_missing_percentage'] = round(
            (missing_analysis['total_missing_cells'] / missing_analysis['total_cells']) * 100, 2
            if missing_analysis['total_cells'] > 0 else 0.0
        )
        
        logger.info(
            f"Missing value analysis: {missing_analysis['total_missing_cells']} missing cells "
            f"({missing_analysis['overall_missing_percentage']}%)"
        )
        return missing_analysis
    
    def analyze_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze duplicate records in the dataset.
        
        Args:
            df: DataFrame to analyze.
            
        Returns:
            Dict[str, Any]: Duplicate analysis results.
        """
        duplicate_mask = df.duplicated(keep=False)
        duplicate_count = duplicate_mask.sum()
        unique_duplicate_count = df.duplicated().sum()
        
        duplicate_analysis = {
            'total_duplicate_rows': int(duplicate_count),
            'unique_duplicate_records': int(unique_duplicate_count),
            'duplicate_percentage': round((unique_duplicate_count / len(df)) * 100, 2) if len(df) > 0 else 0.0,
            'has_duplicates': unique_duplicate_count > 0,
        }
        
        logger.info(
            f"Duplicate analysis: {unique_duplicate_count} duplicate records "
            f"({duplicate_analysis['duplicate_percentage']}%)"
        )
        return duplicate_analysis
    
    def generate_statistical_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate statistical summary for numerical columns.
        
        Args:
            df: DataFrame to analyze.
            
        Returns:
            Dict[str, Any]: Statistical summary by column.
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        summary = {}
        
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                summary[col] = {
                    'count': int(len(col_data)),
                    'mean': round(float(col_data.mean()), 4),
                    'median': round(float(col_data.median()), 4),
                    'std': round(float(col_data.std()), 4),
                    'min': round(float(col_data.min()), 4),
                    'max': round(float(col_data.max()), 4),
                    'q1': round(float(col_data.quantile(0.25)), 4),
                    'q2': round(float(col_data.quantile(0.50)), 4),
                    'q3': round(float(col_data.quantile(0.75)), 4),
                    'iqr': round(float(col_data.quantile(0.75) - col_data.quantile(0.25)), 4),
                }
        
        logger.info(f"Generated statistical summary for {len(summary)} numeric columns")
        return summary
    
    def generate_data_quality_report(self, df: pd.DataFrame, 
                                    report_path: Optional[Path] = None) -> str:
        """
        Generate comprehensive data quality report and save to file.
        
        Args:
            df: DataFrame to analyze.
            report_path: Optional custom report path. Uses config default if not provided.
            
        Returns:
            str: Report content as string.
        """
        report_path = report_path or config.QUALITY_REPORT_FILE
        
        overview = self.generate_dataset_overview(df)
        missing = self.analyze_missing_values(df)
        duplicates = self.analyze_duplicates(df)
        stats = self.generate_statistical_summary(df)
        
        # Store metrics for later use
        self.quality_metrics = {
            'overview': overview,
            'missing_values': missing,
            'duplicates': duplicates,
            'statistics': stats,
        }
        
        # Build report
        lines = []
        lines.append(config.SEPARATOR)
        lines.append(" " * 20 + "DATA QUALITY REPORT")
        lines.append(" " * 15 + "E-Commerce Data Cleaning Pipeline")
        lines.append(config.SEPARATOR)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Dataset Overview
        lines.append("─" * config.REPORT_WIDTH)
        lines.append("1. DATASET OVERVIEW")
        lines.append("─" * config.REPORT_WIDTH)
        lines.append(f"  Total Rows:          {overview['total_rows']:,}")
        lines.append(f"  Total Columns:       {overview['total_columns']}")
        lines.append(f"  Memory Usage:        {overview['memory_usage_mb']:.2f} MB")
        lines.append("")
        lines.append("  Column Names & Data Types:")
        for col, dtype in overview['dtypes'].items():
            lines.append(f"    {col:<25} {dtype}")
        lines.append("")
        
        # Missing Values Analysis
        lines.append("─" * config.REPORT_WIDTH)
        lines.append("2. MISSING VALUES ANALYSIS")
        lines.append("─" * config.REPORT_WIDTH)
        lines.append(f"  Total Missing Cells: {missing['total_missing_cells']:,}")
        lines.append(f"  Total Cells:         {missing['total_cells']:,}")
        lines.append(f"  Overall Missing %:   {missing['overall_missing_percentage']:.2f}%")
        lines.append("")
        lines.append("  Per Column Breakdown:")
        lines.append(f"    {'Column':<25} {'Missing':>10} {'%':>8} {'Type':>15}")
        lines.append("    " + "-" * 60)
        for col, metrics in missing['per_column'].items():
            status = "HIGH" if metrics['missing_percentage'] > config.MAX_MISSING_PERCENTAGE else "OK"
            lines.append(
                f"    {col:<25} {metrics['missing_count']:>10,} "
                f"{metrics['missing_percentage']:>7.2f}% {status:>15}"
            )
        lines.append("")
        
        # Duplicate Analysis
        lines.append("─" * config.REPORT_WIDTH)
        lines.append("3. DUPLICATE ANALYSIS")
        lines.append("─" * config.REPORT_WIDTH)
        lines.append(f"  Duplicate Records:   {duplicates['unique_duplicate_records']:,}")
        lines.append(f"  Duplicate %:         {duplicates['duplicate_percentage']:.2f}%")
        lines.append(f"  Status:              {'⚠️  ISSUES FOUND' if duplicates['has_duplicates'] else '✅  NO DUPLICATES'}")
        lines.append("")
        
        # Statistical Summary
        lines.append("─" * config.REPORT_WIDTH)
        lines.append("4. STATISTICAL SUMMARY (NUMERIC COLUMNS)")
        lines.append("─" * config.REPORT_WIDTH)
        if stats:
            for col, metrics in stats.items():
                lines.append(f"  Column: {col}")
                lines.append(f"    Count:    {metrics['count']:,}")
                lines.append(f"    Mean:     {metrics['mean']}")
                lines.append(f"    Median:   {metrics['median']}")
                lines.append(f"    Std Dev:  {metrics['std']}")
                lines.append(f"    Min:      {metrics['min']}")
                lines.append(f"    Max:      {metrics['max']}")
                lines.append(f"    Q1:       {metrics['q1']}")
                lines.append(f"    Q2:       {metrics['q2']}")
                lines.append(f"    Q3:       {metrics['q3']}")
                lines.append(f"    IQR:      {metrics['iqr']}")
                lines.append("")
        else:
            lines.append("  No numeric columns found for statistical analysis.")
            lines.append("")
        
        lines.append(config.SEPARATOR)
        lines.append("END OF DATA QUALITY REPORT")
        lines.append(config.SEPARATOR)
        
        report_content = "\n".join(lines)
        
        # Save report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding=config.ENCODING) as f:
            f.write(report_content)
        
        logger.info(f"Data quality report saved to: {report_path}")
        return report_content
    
    def generate_cleaning_summary(self, 
                                   before_df: pd.DataFrame,
                                   after_df: pd.DataFrame,
                                   cleaning_stats: Dict[str, Any],
                                   report_path: Optional[Path] = None) -> str:
        """
        Generate cleaning summary report comparing before and after states.
        
        Args:
            before_df: DataFrame before cleaning.
            after_df: DataFrame after cleaning.
            cleaning_stats: Dictionary with cleaning operation statistics.
            report_path: Optional custom report path.
            
        Returns:
            str: Cleaning summary report content.
        """
        report_path = report_path or config.CLEANING_SUMMARY_FILE
        
        # Calculate before metrics
        before_missing = self.analyze_missing_values(before_df)
        before_duplicates = self.analyze_duplicates(before_df)
        
        # Calculate after metrics
        after_missing = self.analyze_missing_values(after_df)
        after_duplicates = self.analyze_duplicates(after_df)
        
        # Store metrics
        self.cleaning_metrics = {
            'before': {
                'total_rows': len(before_df),
                'total_columns': len(before_df.columns),
                'missing_values': before_missing['total_missing_cells'],
                'duplicate_records': before_duplicates['unique_duplicate_records'],
            },
            'after': {
                'total_rows': len(after_df),
                'total_columns': len(after_df.columns),
                'missing_values': after_missing['total_missing_cells'],
                'duplicate_records': after_duplicates['unique_duplicate_records'],
            },
            'improvements': cleaning_stats,
        }
        
        # Build report
        lines = []
        lines.append(config.SEPARATOR)
        lines.append(" " * 20 + "DATA CLEANING SUMMARY REPORT")
        lines.append(" " * 15 + "E-Commerce Data Cleaning Pipeline")
        lines.append(config.SEPARATOR)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Before Cleaning
        lines.append("─" * config.REPORT_WIDTH)
        lines.append("BEFORE CLEANING")
        lines.append("─" * config.REPORT_WIDTH)
        lines.append(f"  Total Rows:          {len(before_df):,}")
        lines.append(f"  Total Columns:       {len(before_df.columns)}")
        lines.append(f"  Missing Values:      {before_missing['total_missing_cells']:,}")
        lines.append(f"  Duplicate Records:   {before_duplicates['unique_duplicate_records']:,}")
        lines.append("")
        
        # After Cleaning
        lines.append("─" * config.REPORT_WIDTH)
        lines.append("AFTER CLEANING")
        lines.append("─" * config.REPORT_WIDTH)
        lines.append(f"  Total Rows:          {len(after_df):,}")
        lines.append(f"  Total Columns:       {len(after_df.columns)}")
        lines.append(f"  Missing Values:      {after_missing['total_missing_cells']:,}")
        lines.append(f"  Duplicate Records:   {after_duplicates['unique_duplicate_records']:,}")
        lines.append("")
        
        # Improvement Summary
        lines.append("─" * config.REPORT_WIDTH)
        lines.append("IMPROVEMENT SUMMARY")
        lines.append("─" * config.REPORT_WIDTH)
        
        rows_removed = len(before_df) - len(after_df)
        missing_fixed = before_missing['total_missing_cells'] - after_missing['total_missing_cells']
        duplicates_removed = before_duplicates['unique_duplicate_records'] - after_duplicates['unique_duplicate_records']
        
        lines.append(f"  Rows Removed:              {rows_removed:,}")
        lines.append(f"  Missing Values Fixed:      {missing_fixed:,}")
        lines.append(f"  Duplicate Records Removed:   {duplicates_removed:,}")
        lines.append("")
        
        # Detailed cleaning stats
        if cleaning_stats:
            lines.append("─" * config.REPORT_WIDTH)
            lines.append("DETAILED CLEANING OPERATIONS")
            lines.append("─" * config.REPORT_WIDTH)
            for operation, count in cleaning_stats.items():
                lines.append(f"  {operation:<40} {count:>10,}")
            lines.append("")
        
        lines.append("─" * config.REPORT_WIDTH)
        lines.append("QUALITY SCORE")
        lines.append("─" * config.REPORT_WIDTH)
        
        # Calculate quality scores
        before_quality = max(0, 100 - before_missing['overall_missing_percentage'] - before_duplicates['duplicate_percentage'])
        after_quality = max(0, 100 - after_missing['overall_missing_percentage'] - after_duplicates['duplicate_percentage'])
        
        lines.append(f"  Before Cleaning:   {before_quality:.2f}%")
        lines.append(f"  After Cleaning:    {after_quality:.2f}%")
        lines.append(f"  Improvement:       +{after_quality - before_quality:.2f}%")
        lines.append("")
        
        lines.append(config.SEPARATOR)
        lines.append("END OF CLEANING SUMMARY REPORT")
        lines.append(config.SEPARATOR)
        
        report_content = "\n".join(lines)
        
        # Save report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding=config.ENCODING) as f:
            f.write(report_content)
        
        logger.info(f"Cleaning summary report saved to: {report_path}")
        return report_content
    
    def get_quality_metrics(self) -> Dict[str, Any]:
        """Get stored quality metrics."""
        return self.quality_metrics.copy()
    
    def get_cleaning_metrics(self) -> Dict[str, Any]:
        """Get stored cleaning metrics."""
        return self.cleaning_metrics.copy()