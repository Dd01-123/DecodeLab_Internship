import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

from app.cleaning.config import config


logger = logging.getLogger(__name__)

# Set style for professional visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class DistributionAnalyzer:
    """
    Enterprise-grade distribution analyzer with automatic classification.
    
    Generates publication-quality visualizations and classifies
    distributions as Normal, Right Skewed, Left Skewed, or Uniform.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with dataset.
        
        Args:
            df: DataFrame to analyze.
        """
        self.df = df.copy()
        self.numeric_columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
        self.distribution_results: Dict[str, Dict[str, Any]] = {}
        self.viz_dir = config.BASE_DIR / 'visualizations' / 'distributions'
        
    def classify_distribution(self, series: pd.Series) -> Dict[str, Any]:
        """
        Classify distribution shape based on statistical tests.
        
        Uses skewness, kurtosis, and normality tests to classify
        the distribution type.
        
        Args:
            series: Numeric Series to classify.
            
        Returns:
            Dict with classification results.
        """
        clean_series = series.dropna()
        
        if len(clean_series) < 8:
            return {'classification': 'Insufficient Data', 'confidence': 0.0}
        
        # Calculate skewness
        skewness = stats.skew(clean_series)
        
        # Normality test (Shapiro-Wilk for small samples, D'Agostino for larger)
        if len(clean_series) <= 5000:
            try:
                stat, p_value = stats.shapiro(clean_series)
                is_normal = p_value > 0.05
                normality_test = 'Shapiro-Wilk'
            except Exception:
                stat, p_value = stats.normaltest(clean_series)
                is_normal = p_value > 0.05
                normality_test = "D'Agostino"
        else:
            stat, p_value = stats.normaltest(clean_series)
            is_normal = p_value > 0.05
            normality_test = "D'Agostino"
        
        # Classification logic
        if is_normal and abs(skewness) < 0.5:
            classification = 'Normal'
            confidence = min(p_value, 1.0)
        elif skewness > 1.0:
            classification = 'Right Skewed (Positive)'
            confidence = min(abs(skewness) / 3, 1.0)
        elif skewness > 0.5:
            classification = 'Moderately Right Skewed'
            confidence = min(abs(skewness) / 2, 1.0)
        elif skewness < -1.0:
            classification = 'Left Skewed (Negative)'
            confidence = min(abs(skewness) / 3, 1.0)
        elif skewness < -0.5:
            classification = 'Moderately Left Skewed'
            confidence = min(abs(skewness) / 2, 1.0)
        else:
            # Check for uniform-like distribution
            kurt = stats.kurtosis(clean_series)
            if abs(kurt) < 1.0 and abs(skewness) < 0.3:
                classification = 'Approximately Uniform'
                confidence = 0.6
            else:
                classification = 'Approximately Normal'
                confidence = min(p_value, 0.8)
        
        return {
            'classification': classification,
            'confidence': round(float(confidence), 4),
            'skewness': round(float(skewness), 4),
            'kurtosis': round(float(stats.kurtosis(clean_series)), 4),
            'normality_test': normality_test,
            'normality_p_value': round(float(p_value), 6),
            'is_normal': is_normal,
            'sample_size': int(len(clean_series)),
        }
    
    def generate_distribution_plot(self, column_name: str, 
                                    save_path: Optional[Path] = None) -> Path:
        """
        Generate histogram with KDE overlay for a single column.
        
        Args:
            column_name: Column to visualize.
            save_path: Optional path to save figure.
            
        Returns:
            Path to saved figure.
        """
        if column_name not in self.numeric_columns:
            logger.warning(f"Column '{column_name}' is not numeric, skipping")
            return None
        
        series = self.df[column_name].dropna()
        
        if len(series) == 0:
            logger.warning(f"Column '{column_name}' has no valid data, skipping")
            return None
        
        # Classification
        classification = self.classify_distribution(series)
        self.distribution_results[column_name] = classification
        
        # Create figure with two subplots
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle(f'Distribution Analysis: {column_name}', fontsize=14, fontweight='bold')
        
        # Histogram with KDE
        ax1 = axes[0]
        sns.histplot(series, kde=True, ax=ax1, color='steelblue', alpha=0.7, stat='density')
        ax1.axvline(series.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {series.mean():.2f}')
        ax1.axvline(series.median(), color='green', linestyle='--', linewidth=2, label=f'Median: {series.median():.2f}')
        ax1.set_title('Histogram with KDE')
        ax1.set_xlabel(column_name)
        ax1.set_ylabel('Density')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Q-Q plot for normality assessment
        ax2 = axes[1]
        stats.probplot(series, dist="norm", plot=ax2)
        ax2.set_title('Q-Q Plot (Normal Distribution)')
        ax2.grid(True, alpha=0.3)
        
        # Add classification info as text
        info_text = (
            f"Classification: {classification['classification']}\n"
            f"Confidence: {classification['confidence']:.2%}\n"
            f"Skewness: {classification['skewness']:.4f}\n"
            f"Kurtosis: {classification['kurtosis']:.4f}\n"
            f"Normality p-value: {classification['normality_p_value']:.6f}"
        )
        fig.text(0.5, 0.02, info_text, ha='center', fontsize=9, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout(rect=[0, 0.08, 1, 0.95])
        
        # Save figure
        if save_path is None:
            save_path = self.viz_dir / f'{column_name}_distribution.png'
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        logger.info(f"Distribution plot saved for '{column_name}': {save_path}")
        return save_path
    
    def analyze_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Generate distribution analysis for all numeric columns.
        
        Returns:
            Dict mapping column names to classification results.
        """
        logger.info(f"Analyzing distributions for {len(self.numeric_columns)} columns...")
        
        for col in self.numeric_columns:
            self.generate_distribution_plot(col)
        
        logger.info(f"Distribution analysis complete. Generated {len(self.distribution_results)} plots")
        return self.distribution_results.copy()
    
    def get_distribution_summary(self) -> pd.DataFrame:
        """
        Get distribution summary as DataFrame.
        
        Returns:
            pd.DataFrame: Summary of all distribution classifications.
        """
        if not self.distribution_results:
            self.analyze_all()
        
        rows = []
        for col, result in self.distribution_results.items():
            rows.append({
                'Column': col,
                'Classification': result['classification'],
                'Confidence': result['confidence'],
                'Skewness': result['skewness'],
                'Kurtosis': result['kurtosis'],
                'Is_Normal': result['is_normal'],
                'P_Value': result['normality_p_value'],
            })
        
        return pd.DataFrame(rows)
    
    def get_results(self) -> Dict[str, Dict[str, Any]]:
        """Get distribution analysis results."""
        if not self.distribution_results:
            self.analyze_all()
        return self.distribution_results.copy()
