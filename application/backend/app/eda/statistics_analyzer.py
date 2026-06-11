import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from scipy import stats

from app.cleaning.config import config


logger = logging.getLogger(__name__)


class StatisticsAnalyzer:
    """
    Enterprise-grade descriptive statistics analyzer.
    
    Automatically detects numeric columns and computes comprehensive
    statistical summaries with distribution shape analysis.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with dataset.
        
        Args:
            df: DataFrame to analyze.
        """
        self.df = df.copy()
        self.numeric_columns = self._get_numeric_columns()
        self.statistics: Dict[str, Dict[str, Any]] = {}
        
    def _get_numeric_columns(self) -> List[str]:
        """
        Automatically identify all numeric columns.
        
        Returns:
            List of numeric column names.
        """
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        logger.info(f"Identified {len(numeric_cols)} numeric columns: {numeric_cols}")
        return numeric_cols
    
    def calculate_basic_stats(self, series: pd.Series) -> Dict[str, Any]:
        """
        Calculate basic descriptive statistics for a series.
        
        Args:
            series: Numeric Series to analyze.
            
        Returns:
            Dict with basic statistics.
        """
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return {'error': 'No valid data'}
        
        return {
            'count': int(len(clean_series)),
            'mean': round(float(clean_series.mean()), 4),
            'median': round(float(clean_series.median()), 4),
            'mode': self._calculate_mode(clean_series),
            'min': round(float(clean_series.min()), 4),
            'max': round(float(clean_series.max()), 4),
            'range': round(float(clean_series.max() - clean_series.min()), 4),
        }
    
    def _calculate_mode(self, series: pd.Series) -> Any:
        """
        Calculate mode with fallback for multi-modal data.
        
        Args:
            series: Series to analyze.
            
        Returns:
            Mode value or list of modes.
        """
        try:
            mode_result = series.mode()
            if len(mode_result) == 1:
                return round(float(mode_result.iloc[0]), 4) if pd.api.types.is_numeric_dtype(series) else str(mode_result.iloc[0])
            elif len(mode_result) > 1:
                return [round(float(v), 4) if pd.api.types.is_numeric_dtype(series) else str(v) for v in mode_result.tolist()]
            return None
        except Exception:
            return None
    
    def calculate_dispersion(self, series: pd.Series) -> Dict[str, Any]:
        """
        Calculate dispersion measures.
        
        Args:
            series: Numeric Series to analyze.
            
        Returns:
            Dict with dispersion statistics.
        """
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return {'error': 'No valid data'}
        
        variance = clean_series.var()
        std_dev = clean_series.std()
        
        return {
            'variance': round(float(variance), 4) if pd.notna(variance) else None,
            'std_deviation': round(float(std_dev), 4) if pd.notna(std_dev) else None,
            'cv': round(float(std_dev / clean_series.mean()), 4) if clean_series.mean() != 0 else None,
        }
    
    def calculate_quartiles(self, series: pd.Series) -> Dict[str, Any]:
        """
        Calculate quartiles and IQR.
        
        Args:
            series: Numeric Series to analyze.
            
        Returns:
            Dict with quartile statistics.
        """
        clean_series = series.dropna()
        
        if len(clean_series) == 0:
            return {'error': 'No valid data'}
        
        q1 = clean_series.quantile(0.25)
        q2 = clean_series.quantile(0.50)
        q3 = clean_series.quantile(0.75)
        iqr = q3 - q1
        
        return {
            'q1': round(float(q1), 4),
            'q2': round(float(q2), 4),
            'q3': round(float(q3), 4),
            'iqr': round(float(iqr), 4),
            'p5': round(float(clean_series.quantile(0.05)), 4),
            'p95': round(float(clean_series.quantile(0.95)), 4),
            'p99': round(float(clean_series.quantile(0.99)), 4),
        }
    
    def calculate_shape(self, series: pd.Series) -> Dict[str, Any]:
        """
        Calculate distribution shape measures (skewness, kurtosis).
        
        Args:
            series: Numeric Series to analyze.
            
        Returns:
            Dict with shape statistics.
        """
        clean_series = series.dropna()
        
        if len(clean_series) < 3:
            return {'error': 'Insufficient data (need >= 3 values)'}
        
        try:
            skewness = stats.skew(clean_series)
            kurtosis = stats.kurtosis(clean_series)
            
            # Classify skewness
            if abs(skewness) < 0.5:
                skew_type = "Approximately Symmetric"
            elif skewness > 0.5:
                skew_type = "Right Skewed (Positive)"
            else:
                skew_type = "Left Skewed (Negative)"
            
            # Classify kurtosis
            if abs(kurtosis) < 0.5:
                kurt_type = "Mesokurtic (Normal)"
            elif kurtosis > 0.5:
                kurt_type = "Leptokurtic (Heavy Tails)"
            else:
                kurt_type = "Platykurtic (Light Tails)"
            
            return {
                'skewness': round(float(skewness), 4),
                'skewness_type': skew_type,
                'kurtosis': round(float(kurtosis), 4),
                'kurtosis_type': kurt_type,
            }
        except Exception as e:
            logger.warning(f"Error calculating shape statistics: {str(e)}")
            return {'error': str(e)}
    
    def analyze_column(self, column_name: str) -> Dict[str, Any]:
        """
        Run complete statistical analysis on a single column.
        
        Args:
            column_name: Name of column to analyze.
            
        Returns:
            Dict with all statistics for the column.
        """
        if column_name not in self.numeric_columns:
            logger.warning(f"Column '{column_name}' is not numeric, skipping")
            return {}
        
        series = self.df[column_name]
        
        column_stats = {
            'column_name': column_name,
            'basic': self.calculate_basic_stats(series),
            'dispersion': self.calculate_dispersion(series),
            'quartiles': self.calculate_quartiles(series),
            'shape': self.calculate_shape(series),
        }
        
        return column_stats
    
    def analyze_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Run complete statistical analysis on all numeric columns.
        
        Returns:
            Dict mapping column names to their statistics.
        """
        logger.info(f"Running descriptive statistics on {len(self.numeric_columns)} columns...")
        
        for col in self.numeric_columns:
            self.statistics[col] = self.analyze_column(col)
        
        logger.info("Descriptive statistics analysis complete")
        return self.statistics.copy()
    
    def save_statistics_csv(self, output_path: Optional[Path] = None) -> Path:
        """
        Save statistics to CSV format for easy viewing.
        
        Args:
            output_path: Path to save CSV. Uses default if not provided.
            
        Returns:
            Path to saved file.
        """
        output_path = output_path or (config.REPORTS_DIR / 'eda' / 'descriptive_statistics.csv')
        
        if not self.statistics:
            self.analyze_all()
        
        rows = []
        for col_name, stats in self.statistics.items():
            if 'error' in stats.get('basic', {}):
                continue
            
            row = {'Column': col_name}
            
            # Basic stats
            basic = stats.get('basic', {})
            row.update({
                'Count': basic.get('count'),
                'Mean': basic.get('mean'),
                'Median': basic.get('median'),
                'Mode': str(basic.get('mode', 'N/A')),
                'Min': basic.get('min'),
                'Max': basic.get('max'),
                'Range': basic.get('range'),
            })
            
            # Dispersion
            dispersion = stats.get('dispersion', {})
            row.update({
                'Variance': dispersion.get('variance'),
                'Std_Deviation': dispersion.get('std_deviation'),
                'CV': dispersion.get('cv'),
            })
            
            # Quartiles
            quartiles = stats.get('quartiles', {})
            row.update({
                'Q1': quartiles.get('q1'),
                'Q2': quartiles.get('q2'),
                'Q3': quartiles.get('q3'),
                'IQR': quartiles.get('iqr'),
                'P5': quartiles.get('p5'),
                'P95': quartiles.get('p95'),
                'P99': quartiles.get('p99'),
            })
            
            # Shape
            shape = stats.get('shape', {})
            row.update({
                'Skewness': shape.get('skewness'),
                'Skewness_Type': shape.get('skewness_type'),
                'Kurtosis': shape.get('kurtosis'),
                'Kurtosis_Type': shape.get('kurtosis_type'),
            })
            
            rows.append(row)
        
        df_stats = pd.DataFrame(rows)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_stats.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"Descriptive statistics saved to: {output_path}")
        return output_path
    
    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get calculated statistics."""
        if not self.statistics:
            self.analyze_all()
        return self.statistics.copy()
