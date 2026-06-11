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
plt.rcParams['figure.figsize'] = (12, 10)


class CorrelationAnalyzer:
    """
    Enterprise-grade correlation analyzer with multiple methods.
    
    Computes Pearson and Spearman correlations, generates heatmaps,
    and identifies significant relationships in the data.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with dataset.
        
        Args:
            df: DataFrame to analyze.
        """
        self.df = df.copy()
        self.numeric_columns = self.df.select_dtypes(include=[np.number]).columns.tolist()
        self.correlation_results: Dict[str, Any] = {}
        self.viz_dir = config.BASE_DIR / 'visualizations' / 'correlations'
        
    def calculate_pearson(self) -> pd.DataFrame:
        """
        Calculate Pearson correlation matrix (linear relationships).
        
        Returns:
            pd.DataFrame: Pearson correlation matrix.
        """
        if len(self.numeric_columns) < 2:
            logger.warning("Need at least 2 numeric columns for correlation analysis")
            return pd.DataFrame()
        
        numeric_df = self.df[self.numeric_columns]
        corr_matrix = numeric_df.corr(method='pearson')
        
        logger.info(f"Pearson correlation matrix calculated: {corr_matrix.shape}")
        return corr_matrix
    
    def calculate_spearman(self) -> pd.DataFrame:
        """
        Calculate Spearman correlation matrix (monotonic relationships).
        
        Returns:
            pd.DataFrame: Spearman correlation matrix.
        """
        if len(self.numeric_columns) < 2:
            logger.warning("Need at least 2 numeric columns for correlation analysis")
            return pd.DataFrame()
        
        numeric_df = self.df[self.numeric_columns]
        corr_matrix = numeric_df.corr(method='spearman')
        
        logger.info(f"Spearman correlation matrix calculated: {corr_matrix.shape}")
        return corr_matrix
    
    def identify_strong_correlations(self, corr_matrix: pd.DataFrame, 
                                     threshold: float = 0.7) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify strong correlations from a correlation matrix.
        
        Args:
            corr_matrix: Correlation matrix DataFrame.
            threshold: Absolute correlation threshold (default 0.7).
            
        Returns:
            Dict with strong positive, strong negative, and weak correlations.
        """
        strong_positive = []
        strong_negative = []
        weak = []
        
        cols = corr_matrix.columns
        
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                corr_value = corr_matrix.iloc[i, j]
                
                if pd.isna(corr_value):
                    continue
                
                corr_info = {
                    'column_1': cols[i],
                    'column_2': cols[j],
                    'correlation': round(float(corr_value), 4),
                    'abs_correlation': round(abs(float(corr_value)), 4),
                }
                
                if abs(corr_value) >= threshold:
                    if corr_value > 0:
                        strong_positive.append(corr_info)
                    else:
                        strong_negative.append(corr_info)
                elif abs(corr_value) < 0.3:
                    weak.append(corr_info)
        
        # Sort by absolute correlation strength
        strong_positive.sort(key=lambda x: x['abs_correlation'], reverse=True)
        strong_negative.sort(key=lambda x: x['abs_correlation'], reverse=True)
        weak.sort(key=lambda x: x['abs_correlation'], reverse=True)
        
        return {
            'strong_positive': strong_positive,
            'strong_negative': strong_negative,
            'weak': weak,
        }
    
    def generate_heatmap(self, corr_matrix: pd.DataFrame, 
                         method_name: str,
                         save_path: Optional[Path] = None) -> Path:
        """
        Generate correlation heatmap visualization.
        
        Args:
            corr_matrix: Correlation matrix to visualize.
            method_name: Name of correlation method (Pearson/Spearman).
            save_path: Optional path to save figure.
            
        Returns:
            Path to saved figure.
        """
        if corr_matrix.empty:
            logger.warning("Empty correlation matrix, skipping heatmap")
            return None
        
        fig, ax = plt.subplots(figsize=(max(10, len(corr_matrix.columns) * 1.5), 
                                       max(8, len(corr_matrix.columns) * 1.2)))
        
        # Create mask for upper triangle (optional, for cleaner look)
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
        
        # Generate heatmap
        heatmap = sns.heatmap(
            corr_matrix,
            mask=mask,
            annot=True,
            fmt='.3f',
            cmap='RdBu_r',
            center=0,
            square=True,
            linewidths=0.5,
            cbar_kws={"shrink": 0.8},
            ax=ax,
            vmin=-1,
            vmax=1,
        )
        
        ax.set_title(f'{method_name} Correlation Matrix', fontsize=14, fontweight='bold', pad=20)
        
        # Rotate labels for better readability
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = self.viz_dir / f'{method_name.lower()}_correlation_heatmap.png'
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        logger.info(f"{method_name} correlation heatmap saved: {save_path}")
        return save_path
    
    def analyze_all(self) -> Dict[str, Any]:
        """
        Run complete correlation analysis.
        
        Returns:
            Dict with all correlation results.
        """
        logger.info("Starting correlation analysis...")
        
        if len(self.numeric_columns) < 2:
            logger.warning("Insufficient numeric columns for correlation analysis")
            return {}
        
        # Calculate both correlation matrices
        pearson_matrix = self.calculate_pearson()
        spearman_matrix = self.calculate_spearman()
        
        # Identify strong correlations
        pearson_correlations = self.identify_strong_correlations(pearson_matrix, threshold=0.7)
        spearman_correlations = self.identify_strong_correlations(spearman_matrix, threshold=0.7)
        
        # Generate heatmaps
        self.generate_heatmap(pearson_matrix, 'Pearson')
        self.generate_heatmap(spearman_matrix, 'Spearman')
        
        self.correlation_results = {
            'pearson_matrix': pearson_matrix,
            'spearman_matrix': spearman_matrix,
            'pearson_correlations': pearson_correlations,
            'spearman_correlations': spearman_correlations,
            'numeric_columns': self.numeric_columns,
        }
        
        logger.info("Correlation analysis complete")
        return self.correlation_results.copy()
    
    def save_correlation_csv(self, output_path: Optional[Path] = None) -> Path:
        """
        Save correlation matrices to CSV.
        
        Args:
            output_path: Path to save report.
            
        Returns:
            Path to saved file.
        """
        output_path = output_path or (config.REPORTS_DIR / 'eda' / 'correlation_matrix.csv')
        
        if not self.correlation_results:
            self.analyze_all()
        
        # Save Pearson matrix
        pearson_path = output_path.parent / 'pearson_correlation_matrix.csv'
        self.correlation_results['pearson_matrix'].to_csv(pearson_path, encoding='utf-8')
        
        # Save Spearman matrix
        spearman_path = output_path.parent / 'spearman_correlation_matrix.csv'
        self.correlation_results['spearman_matrix'].to_csv(spearman_path, encoding='utf-8')
        
        # Save combined correlation summary
        rows = []
        
        # Strong positive correlations
        for corr in self.correlation_results['pearson_correlations']['strong_positive']:
            rows.append({
                'Type': 'Strong Positive',
                'Method': 'Pearson',
                'Column_1': corr['column_1'],
                'Column_2': corr['column_2'],
                'Correlation': corr['correlation'],
                'Strength': 'Strong',
            })
        
        for corr in self.correlation_results['spearman_correlations']['strong_positive']:
            rows.append({
                'Type': 'Strong Positive',
                'Method': 'Spearman',
                'Column_1': corr['column_1'],
                'Column_2': corr['column_2'],
                'Correlation': corr['correlation'],
                'Strength': 'Strong',
            })
        
        # Strong negative correlations
        for corr in self.correlation_results['pearson_correlations']['strong_negative']:
            rows.append({
                'Type': 'Strong Negative',
                'Method': 'Pearson',
                'Column_1': corr['column_1'],
                'Column_2': corr['column_2'],
                'Correlation': corr['correlation'],
                'Strength': 'Strong',
            })
        
        for corr in self.correlation_results['spearman_correlations']['strong_negative']:
            rows.append({
                'Type': 'Strong Negative',
                'Method': 'Spearman',
                'Column_1': corr['column_1'],
                'Column_2': corr['column_2'],
                'Correlation': corr['correlation'],
                'Strength': 'Strong',
            })
        
        df_summary = pd.DataFrame(rows)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_summary.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"Correlation reports saved to: {output_path.parent}")
        return output_path
    
    def get_results(self) -> Dict[str, Any]:
        """Get correlation analysis results."""
        if not self.correlation_results:
            self.analyze_all()
        return self.correlation_results.copy()
