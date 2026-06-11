import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

from app.cleaning.config import config


logger = logging.getLogger(__name__)


class DatasetProfiler:
    """
    Enterprise-grade dataset profiler for comprehensive data characterization.
    
    Generates detailed profiles of dataset structure, content, and quality
    suitable for analytics and reporting.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize profiler with dataset.
        
        Args:
            df: DataFrame to profile.
        """
        self.df = df.copy()
        self.profile: Dict[str, Any] = {}
        
    def analyze_structure(self) -> Dict[str, Any]:
        """
        Analyze basic dataset structure.
        
        Returns:
            Dict with row count, column count, shape, and memory info.
        """
        structure = {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'shape': self.df.shape,
            'memory_usage_mb': round(self.df.memory_usage(deep=True).sum() / (1024 ** 2), 4),
            'memory_usage_bytes': int(self.df.memory_usage(deep=True).sum()),
            'column_names': list(self.df.columns),
            'timestamp': datetime.now().isoformat(),
        }
        logger.info(f"Dataset structure: {structure['total_rows']} rows, {structure['total_columns']} columns")
        return structure
    
    def analyze_data_types(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze data types for each column with detailed classification.
        
        Returns:
            Dict mapping column names to type information.
        """
        type_info = {}
        
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            
            # Classify column type
            if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                category = 'datetime'
            elif pd.api.types.is_numeric_dtype(self.df[col]):
                category = 'numeric'
            elif pd.api.types.is_string_dtype(self.df[col]):
                category = 'text'
            else:
                category = 'other'
            
            type_info[col] = {
                'pandas_dtype': dtype,
                'category': category,
                'is_numeric': pd.api.types.is_numeric_dtype(self.df[col]),
                'is_datetime': pd.api.types.is_datetime64_any_dtype(self.df[col]),
                'is_categorical': self.df[col].dtype.name == 'category',
            }
        
        logger.info(f"Analyzed data types for {len(type_info)} columns")
        return type_info
    
    def analyze_missing_values(self) -> Dict[str, Any]:
        """
        Comprehensive missing value analysis per column.
        
        Returns:
            Dict with missing value statistics.
        """
        missing_analysis = {
            'total_missing': 0,
            'total_cells': self.df.shape[0] * self.df.shape[1],
            'overall_missing_pct': 0.0,
            'per_column': {},
        }
        
        for col in self.df.columns:
            missing_count = self.df[col].isna().sum()
            missing_pct = round((missing_count / len(self.df)) * 100, 2) if len(self.df) > 0 else 0.0
            
            missing_analysis['per_column'][col] = {
                'missing_count': int(missing_count),
                'missing_percentage': missing_pct,
                'non_missing_count': int(len(self.df) - missing_count),
                'completeness': round(100 - missing_pct, 2),
            }
            
            missing_analysis['total_missing'] += missing_count
        
        missing_analysis['overall_missing_pct'] = round(
            (missing_analysis['total_missing'] / missing_analysis['total_cells']) * 100, 2
            if missing_analysis['total_cells'] > 0 else 0.0
        )
        
        logger.info(f"Missing values: {missing_analysis['total_missing']} cells ({missing_analysis['overall_missing_pct']}%)")
        return missing_analysis
    
    def analyze_cardinality(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze cardinality (unique value counts) for each column.
        
        Returns:
            Dict with cardinality statistics per column.
        """
        cardinality = {}
        
        for col in self.df.columns:
            unique_count = self.df[col].nunique(dropna=False)
            total_count = len(self.df)
            
            cardinality[col] = {
                'unique_values': int(unique_count),
                'total_values': int(total_count),
                'cardinality_ratio': round(unique_count / total_count, 4) if total_count > 0 else 0.0,
                'is_unique': unique_count == total_count,
                'is_constant': unique_count == 1,
                'is_high_cardinality': unique_count / total_count > 0.9,
                'is_low_cardinality': unique_count / total_count < 0.05,
            }
        
        logger.info(f"Cardinality analysis complete for {len(cardinality)} columns")
        return cardinality
    
    def generate_profile(self) -> Dict[str, Any]:
        """
        Generate complete dataset profile by running all analyses.
        
        Returns:
            Dict with complete profile information.
        """
        logger.info("Generating complete dataset profile...")
        
        self.profile = {
            'structure': self.analyze_structure(),
            'data_types': self.analyze_data_types(),
            'missing_values': self.analyze_missing_values(),
            'cardinality': self.analyze_cardinality(),
        }
        
        logger.info("Dataset profile generation complete")
        return self.profile
    
    def save_profile_report(self, report_path: Optional[Path] = None) -> str:
        """
        Generate and save formatted profile report to file.
        
        Args:
            report_path: Path to save report. Uses default if not provided.
            
        Returns:
            str: Report content.
        """
        report_path = report_path or (config.REPORTS_DIR / 'eda' / 'dataset_profile.txt')
        
        if not self.profile:
            self.generate_profile()
        
        lines = []
        lines.append("=" * 80)
        lines.append(" " * 25 + "DATASET PROFILE REPORT")
        lines.append(" " * 20 + "Exploratory Data Analysis Framework")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Structure
        struct = self.profile['structure']
        lines.append("-" * 80)
        lines.append("1. DATASET STRUCTURE")
        lines.append("-" * 80)
        lines.append(f"  Total Rows:       {struct['total_rows']:,}")
        lines.append(f"  Total Columns:    {struct['total_columns']}")
        lines.append(f"  Shape:            {struct['shape']}")
        lines.append(f"  Memory Usage:     {struct['memory_usage_mb']:.4f} MB ({struct['memory_usage_bytes']:,} bytes)")
        lines.append("")
        
        # Data Types
        lines.append("-" * 80)
        lines.append("2. DATA TYPES")
        lines.append("-" * 80)
        lines.append(f"  {'Column':<25} {'Pandas Dtype':<20} {'Category':<12}")
        lines.append("  " + "-" * 57)
        for col, info in self.profile['data_types'].items():
            lines.append(f"  {col:<25} {info['pandas_dtype']:<20} {info['category']:<12}")
        lines.append("")
        
        # Missing Values
        missing = self.profile['missing_values']
        lines.append("-" * 80)
        lines.append("3. MISSING VALUES ANALYSIS")
        lines.append("-" * 80)
        lines.append(f"  Total Missing Cells:    {missing['total_missing']:,}")
        lines.append(f"  Total Cells:            {missing['total_cells']:,}")
        lines.append(f"  Overall Missing %:      {missing['overall_missing_pct']:.2f}%")
        lines.append("")
        lines.append(f"  {'Column':<25} {'Missing':>10} {'%':>8} {'Complete':>10}")
        lines.append("  " + "-" * 55)
        for col, info in missing['per_column'].items():
            status = "OK" if info['missing_percentage'] == 0 else "ISSUE"
            lines.append(
                f"  {col:<25} {info['missing_count']:>10,} "
                f"{info['missing_percentage']:>7.2f}% {info['completeness']:>9.2f}% {status}"
            )
        lines.append("")
        
        # Cardinality
        card = self.profile['cardinality']
        lines.append("-" * 80)
        lines.append("4. CARDINALITY ANALYSIS")
        lines.append("-" * 80)
        lines.append(f"  {'Column':<25} {'Unique':>10} {'Ratio':>10} {'Type':>20}")
        lines.append("  " + "-" * 65)
        for col, info in card.items():
            if info['is_unique']:
                card_type = "UNIQUE (ID)"
            elif info['is_constant']:
                card_type = "CONSTANT"
            elif info['is_high_cardinality']:
                card_type = "HIGH CARDINALITY"
            elif info['is_low_cardinality']:
                card_type = "LOW CARDINALITY"
            else:
                card_type = "NORMAL"
            lines.append(
                f"  {col:<25} {info['unique_values']:>10,} "
                f"{info['cardinality_ratio']:>10.4f} {card_type:>20}"
            )
        lines.append("")
        
        lines.append("=" * 80)
        lines.append("END OF DATASET PROFILE REPORT")
        lines.append("=" * 80)
        
        report_content = "\n".join(lines)
        
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Dataset profile report saved to: {report_path}")
        return report_content
    
    def get_profile(self) -> Dict[str, Any]:
        """Get the generated profile."""
        if not self.profile:
            self.generate_profile()
        return self.profile.copy()
