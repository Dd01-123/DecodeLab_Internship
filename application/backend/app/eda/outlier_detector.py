import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from app.cleaning.config import config


logger = logging.getLogger(__name__)

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class OutlierDetector:
    """
    Enterprise-grade outlier detector using multiple statistical methods.
    
    Supports IQR Method and Z-Score Method with configurable thresholds
    and comprehensive reporting.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize detector with dataset.
        
        Args:
            df: DataFrame to analyze.
        """
        self.df = df.copy()
        self.numeric_columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
        self.outlier_results: Dict[str, Dict[str, Any]] = {}
        self.viz_dir = config.BASE_DIR / 'visualizations' / 'outliers'
        
    def detect_iqr(self, series: pd.Series, 
                   k: float = 1.5) -> Tuple[pd.Series, pd.Series, Dict[str, Any]]:
        """
        Detect outliers using the Interquartile Range (IQR) Method.
        
        Outliers are values below Q1 - k*IQR or above Q3 + k*IQR.
        
        Args:
            series: Numeric Series to analyze.
            k: IQR multiplier (default 1.5 for standard outliers, 3.0 for extreme).
            
        Returns:
            Tuple of (outlier_mask, clean_data, metadata).
        """
        clean_series = series.dropna()
        
        if len(clean_series) < 4:
            return pd.Series(False, index=series.index), series, {'error': 'Insufficient data'}
        
        q1 = clean_series.quantile(0.25)
        q3 = clean_series.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - k * iqr
        upper_bound = q3 + k * iqr
        
        outlier_mask = (series < lower_bound) | (series > upper_bound)
        outlier_count = outlier_mask.sum()
        outlier_pct = (outlier_count / len(series)) * 100 if len(series) > 0 else 0.0
        
        metadata = {
            'method': 'IQR',
            'k': k,
            'q1': round(float(q1), 4),
            'q3': round(float(q3), 4),
            'iqr': round(float(iqr), 4),
            'lower_bound': round(float(lower_bound), 4),
            'upper_bound': round(float(upper_bound), 4),
            'outlier_count': int(outlier_count),
            'outlier_percentage': round(float(outlier_pct), 2),
            'min_outlier': round(float(series[outlier_mask].min()), 4) if outlier_count > 0 else None,
            'max_outlier': round(float(series[outlier_mask].max()), 4) if outlier_count > 0 else None,
            'outlier_values': series[outlier_mask].tolist() if outlier_count > 0 else [],
        }
        
        return outlier_mask, series[~outlier_mask], metadata
    
    def detect_zscore(self, series: pd.Series, 
                      threshold: float = 3.0) -> Tuple[pd.Series, pd.Series, Dict[str, Any]]:
        """
        Detect outliers using the Z-Score Method.
        
        Outliers are values with |z-score| > threshold.
        
        Args:
            series: Numeric Series to analyze.
            threshold: Z-score threshold (default 3.0 for 99.7% coverage).
            
        Returns:
            Tuple of (outlier_mask, clean_data, metadata).
        """
        clean_series = series.dropna()
        
        if len(clean_series) < 3:
            return pd.Series(False, index=series.index), series, {'error': 'Insufficient data'}
        
        mean = clean_series.mean()
        std = clean_series.std()
        
        if std == 0:
            return pd.Series(False, index=series.index), series, {'error': 'Zero standard deviation'}
        
        z_scores = np.abs((series - mean) / std)
        outlier_mask = z_scores > threshold
        outlier_count = outlier_mask.sum()
        outlier_pct = (outlier_count / len(series)) * 100 if len(series) > 0 else 0.0
        
        metadata = {
            'method': 'Z-Score',
            'threshold': threshold,
            'mean': round(float(mean), 4),
            'std': round(float(std), 4),
            'outlier_count': int(outlier_count),
            'outlier_percentage': round(float(outlier_pct), 2),
            'min_outlier': round(float(series[outlier_mask].min()), 4) if outlier_count > 0 else None,
            'max_outlier': round(float(series[outlier_mask].max()), 4) if outlier_count > 0 else None,
            'max_z_score': round(float(z_scores.max()), 4),
            'outlier_values': series[outlier_mask].tolist() if outlier_count > 0 else [],
        }
        
        return outlier_mask, series[~outlier_mask], metadata
    
    def detect_outliers(self, column_name: str) -> Dict[str, Any]:
        """
        Run both outlier detection methods on a column.
        
        Args:
            column_name: Column to analyze.
            
        Returns:
            Dict with combined results from both methods.
        """
        if column_name not in self.numeric_columns:
            logger.warning(f"Column '{column_name}' is not numeric, skipping")
            return {}
        
        series = self.df[column_name]
        
        # IQR Method
        iqr_mask, iqr_clean, iqr_meta = self.detect_iqr(series, k=1.5)
        
        # Z-Score Method
        zscore_mask, zscore_clean, zscore_meta = self.detect_zscore(series, threshold=3.0)
        
        # Combined results
        combined_mask = iqr_mask | zscore_mask
        combined_count = combined_mask.sum()
        
        results = {
            'column': column_name,
            'total_rows': len(series),
            'iqr_method': iqr_meta,
            'zscore_method': zscore_meta,
            'combined': {
                'outlier_count': int(combined_count),
                'outlier_percentage': round((combined_count / len(series)) * 100, 2) if len(series) > 0 else 0.0,
                'method': 'Combined (IQR OR Z-Score)',
            }
        }
        
        self.outlier_results[column_name] = results
        return results
    
    def generate_boxplot(self, column_name: str, 
                         save_path: Optional[Path] = None) -> Path:
        """
        Generate boxplot visualization for outlier detection.
        
        Args:
            column_name: Column to visualize.
            save_path: Optional path to save figure.
            
        Returns:
            Path to saved figure.
        """
        if column_name not in self.numeric_columns:
            return None
        
        series = self.df[column_name].dropna()
        
        if len(series) == 0:
            return None
        
        # Get outlier info
        if column_name not in self.outlier_results:
            self.detect_outliers(column_name)
        
        results = self.outlier_results[column_name]
        iqr_info = results['iqr_method']
        zscore_info = results['zscore_method']
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle(f'Outlier Analysis: {column_name}', fontsize=14, fontweight='bold')
        
        # Boxplot
        ax1 = axes[0]
        bp = ax1.boxplot(series, vert=True, patch_artist=True, widths=0.5)
        bp['boxes'][0].set_facecolor('lightblue')
        bp['boxes'][0].set_alpha(0.7)
        ax1.set_ylabel(column_name)
        ax1.set_title('Boxplot (IQR Method)')
        ax1.grid(True, alpha=0.3)
        
        # Add IQR bounds as horizontal lines
        if 'lower_bound' in iqr_info:
            ax1.axhline(iqr_info['lower_bound'], color='red', linestyle='--', alpha=0.7, label=f'Lower Bound: {iqr_info["lower_bound"]:.2f}')
            ax1.axhline(iqr_info['upper_bound'], color='red', linestyle='--', alpha=0.7, label=f'Upper Bound: {iqr_info["upper_bound"]:.2f}')
        ax1.legend(fontsize=8)
        
        # Violin plot for distribution shape
        ax2 = axes[1]
        parts = ax2.violinplot(series, vert=True, showmeans=True, showmedians=True)
        ax2.set_ylabel(column_name)
        ax2.set_title('Violin Plot (Distribution Shape)')
        ax2.grid(True, alpha=0.3)
        
        # Add statistics text
        stats_text = (
            f"IQR Method:\n"
            f"  Outliers: {iqr_info.get('outlier_count', 0)} ({iqr_info.get('outlier_percentage', 0):.2f}%)\n"
            f"  Bounds: [{iqr_info.get('lower_bound', 'N/A'):.2f}, {iqr_info.get('upper_bound', 'N/A'):.2f}]\n\n"
            f"Z-Score Method:\n"
            f"  Outliers: {zscore_info.get('outlier_count', 0)} ({zscore_info.get('outlier_percentage', 0):.2f}%)\n"
            f"  Threshold: +/- {zscore_info.get('threshold', 3.0)}\n\n"
            f"Combined:\n"
            f"  Total Outliers: {results['combined']['outlier_count']} ({results['combined']['outlier_percentage']:.2f}%)"
        )
        fig.text(0.5, 0.02, stats_text, ha='center', fontsize=9,
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))
        
        plt.tight_layout(rect=[0, 0.12, 1, 0.95])
        
        if save_path is None:
            save_path = self.viz_dir / f'{column_name}_outliers.png'
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        logger.info(f"Outlier boxplot saved for '{column_name}': {save_path}")
        return save_path
    
    def analyze_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Run outlier detection on all numeric columns.
        
        Returns:
            Dict mapping column names to outlier results.
        """
        logger.info(f"Running outlier detection on {len(self.numeric_columns)} columns...")
        
        for col in self.numeric_columns:
            self.detect_outliers(col)
            self.generate_boxplot(col)
        
        logger.info(f"Outlier detection complete for {len(self.outlier_results)} columns")
        return self.outlier_results.copy()
    
    def save_outlier_report(self, output_path: Optional[Path] = None) -> Path:
        """
        Save outlier report to CSV.
        
        Args:
            output_path: Path to save report.
            
        Returns:
            Path to saved file.
        """
        output_path = output_path or (config.REPORTS_DIR / 'eda' / 'outlier_report.csv')
        
        if not self.outlier_results:
            self.analyze_all()
        
        rows = []
        for col, results in self.outlier_results.items():
            iqr = results.get('iqr_method', {})
            zscore = results.get('zscore_method', {})
            combined = results.get('combined', {})
            
            rows.append({
                'Column': col,
                'Total_Rows': results.get('total_rows', 0),
                'IQR_Outlier_Count': iqr.get('outlier_count', 0),
                'IQR_Outlier_Pct': iqr.get('outlier_percentage', 0),
                'IQR_Min_Outlier': iqr.get('min_outlier'),
                'IQR_Max_Outlier': iqr.get('max_outlier'),
                'IQR_Lower_Bound': iqr.get('lower_bound'),
                'IQR_Upper_Bound': iqr.get('upper_bound'),
                'ZScore_Outlier_Count': zscore.get('outlier_count', 0),
                'ZScore_Outlier_Pct': zscore.get('outlier_percentage', 0),
                'ZScore_Max_ZScore': zscore.get('max_z_score'),
                'Combined_Outlier_Count': combined.get('outlier_count', 0),
                'Combined_Outlier_Pct': combined.get('outlier_percentage', 0),
            })
        
        df_report = pd.DataFrame(rows)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_report.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"Outlier report saved to: {output_path}")
        return output_path
    
    def get_results(self) -> Dict[str, Dict[str, Any]]:
        """Get outlier detection results."""
        if not self.outlier_results:
            self.analyze_all()
        return self.outlier_results.copy()
