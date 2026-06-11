import logging
from typing import Dict, List, Any, Optional
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


class CategoricalAnalyzer:
    """
    Enterprise-grade categorical data analyzer.
    
    Generates frequency distributions, identifies dominant and rare categories,
    and creates publication-quality bar charts and pie charts.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize analyzer with dataset.
        
        Args:
            df: DataFrame to analyze.
        """
        self.df = df.copy()
        self.categorical_columns = self._get_categorical_columns()
        self.categorical_results: Dict[str, Dict[str, Any]] = {}
        self.viz_dir = config.BASE_DIR / 'visualizations' / 'categorical'
        
    def _get_categorical_columns(self) -> List[str]:
        """
        Automatically identify categorical columns (object/string type).
        
        Returns:
            List of categorical column names.
        """
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Also consider low-cardinality numeric columns as categorical
        for col in self.df.select_dtypes(include=[np.number]).columns:
            unique_ratio = self.df[col].nunique() / len(self.df)
            if unique_ratio < 0.05 and self.df[col].nunique() <= 20:
                cat_cols.append(col)
        
        logger.info(f"Identified {len(cat_cols)} categorical columns: {cat_cols}")
        return cat_cols
    
    def analyze_column(self, column_name: str) -> Dict[str, Any]:
        """
        Analyze a single categorical column.
        
        Args:
            column_name: Column to analyze.
            
        Returns:
            Dict with frequency analysis results.
        """
        if column_name not in self.categorical_columns:
            logger.warning(f"Column '{column_name}' is not categorical, skipping")
            return {}
        
        series = self.df[column_name].dropna().astype(str)
        series = series[series != '']  # Exclude empty strings
        
        if len(series) == 0:
            return {'error': 'No valid data'}
        
        # Frequency counts
        value_counts = series.value_counts()
        total = len(series)
        
        # Percentage distribution
        percentages = (value_counts / total * 100).round(2)
        
        # Identify top and rare categories
        top_categories = value_counts.head(5).to_dict()
        rare_threshold = total * 0.01  # Less than 1%
        rare_categories = value_counts[value_counts < rare_threshold].to_dict()
        
        # Category diversity
        diversity_index = self._calculate_diversity_index(value_counts, total)
        
        results = {
            'column': column_name,
            'total_records': int(total),
            'unique_categories': int(len(value_counts)),
            'top_categories': {str(k): int(v) for k, v in top_categories.items()},
            'top_percentages': {str(k): float(v) for k, v in percentages.head(5).to_dict().items()},
            'rare_categories': {str(k): int(v) for k, v in rare_categories.items()},
            'rare_count': len(rare_categories),
            'diversity_index': round(diversity_index, 4),
            'frequency_table': value_counts.to_dict(),
            'percentage_table': percentages.to_dict(),
        }
        
        self.categorical_results[column_name] = results
        return results
    
    def _calculate_diversity_index(self, value_counts: pd.Series, total: int) -> float:
        """
        Calculate Simpson's Diversity Index (1 - sum of squared proportions).
        
        Args:
            value_counts: Value counts Series.
            total: Total count.
            
        Returns:
            float: Diversity index (0 = no diversity, 1 = maximum diversity).
        """
        if total == 0:
            return 0.0
        
        proportions = value_counts / total
        simpson_index = 1 - sum(proportions ** 2)
        
        return float(simpson_index)
    
    def generate_bar_chart(self, column_name: str, 
                           top_n: int = 15,
                           save_path: Optional[Path] = None) -> Path:
        """
        Generate horizontal bar chart for categorical frequencies.
        
        Args:
            column_name: Column to visualize.
            top_n: Number of top categories to show.
            save_path: Optional path to save figure.
            
        Returns:
            Path to saved figure.
        """
        if column_name not in self.categorical_results:
            self.analyze_column(column_name)
        
        results = self.categorical_results[column_name]
        
        if 'error' in results:
            return None
        
        freq_table = pd.Series(results['frequency_table'])
        
        # Get top N categories
        top_categories = freq_table.head(top_n)
        
        fig, ax = plt.subplots(figsize=(12, max(6, len(top_categories) * 0.4)))
        
        colors = sns.color_palette("husl", len(top_categories))
        bars = ax.barh(range(len(top_categories)), top_categories.values, color=colors)
        
        ax.set_yticks(range(len(top_categories)))
        ax.set_yticklabels([str(cat)[:30] for cat in top_categories.index])
        ax.set_xlabel('Frequency', fontsize=11)
        ax.set_title(f'Categorical Distribution: {column_name} (Top {top_n})', 
                    fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add value labels on bars
        for i, (bar, val) in enumerate(zip(bars, top_categories.values)):
            ax.text(val + max(top_categories.values) * 0.01, i, 
                   f'{val:,} ({val/sum(freq_table)*100:.1f}%)', 
                   va='center', fontsize=9)
        
        # Add diversity info
        info_text = f"Unique Categories: {results['unique_categories']} | Diversity Index: {results['diversity_index']:.4f}"
        fig.text(0.5, 0.02, info_text, ha='center', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        if save_path is None:
            save_path = self.viz_dir / f'{column_name}_bar_chart.png'
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        logger.info(f"Bar chart saved for '{column_name}': {save_path}")
        return save_path
    
    def generate_pie_chart(self, column_name: str,
                           top_n: int = 8,
                           save_path: Optional[Path] = None) -> Path:
        """
        Generate pie chart for categorical distribution.
        
        Args:
            column_name: Column to visualize.
            top_n: Number of top categories to show (others grouped).
            save_path: Optional path to save figure.
            
        Returns:
            Path to saved figure.
        """
        if column_name not in self.categorical_results:
            self.analyze_column(column_name)
        
        results = self.categorical_results[column_name]
        
        if 'error' in results:
            return None
        
        freq_table = pd.Series(results['frequency_table'])
        
        # Get top N and group others
        top_categories = freq_table.head(top_n)
        others_count = freq_table.iloc[top_n:].sum()
        
        if others_count > 0:
            plot_data = pd.concat([top_categories, pd.Series({'Others': others_count})])
        else:
            plot_data = top_categories
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors = sns.color_palette("Set3", len(plot_data))
        wedges, texts, autotexts = ax.pie(
            plot_data.values,
            labels=plot_data.index,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 10},
        )
        
        ax.set_title(f'Distribution: {column_name}', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = self.viz_dir / f'{column_name}_pie_chart.png'
        
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        logger.info(f"Pie chart saved for '{column_name}': {save_path}")
        return save_path
    
    def analyze_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze all categorical columns.
        
        Returns:
            Dict mapping column names to analysis results.
        """
        logger.info(f"Analyzing {len(self.categorical_columns)} categorical columns...")
        
        for col in self.categorical_columns:
            self.analyze_column(col)
            self.generate_bar_chart(col)
            
            # Only generate pie chart if reasonable number of categories
            if self.categorical_results[col].get('unique_categories', 0) <= 15:
                self.generate_pie_chart(col)
        
        logger.info(f"Categorical analysis complete for {len(self.categorical_results)} columns")
        return self.categorical_results.copy()
    
    def save_categorical_summary(self, output_path: Optional[Path] = None) -> Path:
        """
        Save categorical summary to CSV.
        
        Args:
            output_path: Path to save report.
            
        Returns:
            Path to saved file.
        """
        output_path = output_path or (config.REPORTS_DIR / 'eda' / 'categorical_summary.csv')
        
        if not self.categorical_results:
            self.analyze_all()
        
        rows = []
        for col, results in self.categorical_results.items():
            if 'error' in results:
                continue
            
            row = {
                'Column': col,
                'Total_Records': results['total_records'],
                'Unique_Categories': results['unique_categories'],
                'Diversity_Index': results['diversity_index'],
                'Rare_Categories_Count': results['rare_count'],
                'Top_Category': list(results['top_categories'].keys())[0] if results['top_categories'] else 'N/A',
                'Top_Category_Count': list(results['top_categories'].values())[0] if results['top_categories'] else 0,
                'Top_Category_Pct': list(results['top_percentages'].values())[0] if results['top_percentages'] else 0,
            }
            rows.append(row)
        
        df_summary = pd.DataFrame(rows)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_summary.to_csv(output_path, index=False, encoding='utf-8')
        
        logger.info(f"Categorical summary saved to: {output_path}")
        return output_path
    
    def get_results(self) -> Dict[str, Dict[str, Any]]:
        """Get categorical analysis results."""
        if not self.categorical_results:
            self.analyze_all()
        return self.categorical_results.copy()
