import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np

from app.cleaning.config import config
from app.cleaning.data_loader import DataLoader

from app.eda.profiler import DatasetProfiler
from app.eda.statistics_analyzer import StatisticsAnalyzer
from app.eda.distribution_analyzer import DistributionAnalyzer
from app.eda.outlier_detector import OutlierDetector
from app.eda.correlation_analyzer import CorrelationAnalyzer
from app.eda.categorical_analyzer import CategoricalAnalyzer
from app.eda.trend_analyzer import TrendAnalyzer
from app.eda.business_insight_generator import BusinessInsightGenerator


logger = logging.getLogger(__name__)


class EDAPipelineError(Exception):
    """Custom exception for EDA pipeline errors."""
    pass


class EDAPipeline:
    """
    Enterprise-grade EDA pipeline orchestrator.
    
    Coordinates all exploratory data analysis operations in a defined
    sequence with comprehensive logging, error handling, and reporting.
    """
    
    def __init__(self, 
                 data_file_path: Optional[Path] = None):
        """
        Initialize the EDA pipeline.
        
        Args:
            data_file_path: Path to cleaned dataset. Uses config default if not provided.
        """
        self.data_file_path = data_file_path or config.CLEANED_DATA_FILE
        
        # Data container
        self.df: Optional[pd.DataFrame] = None
        
        # Analysis components
        self.profiler: Optional[DatasetProfiler] = None
        self.statistics_analyzer: Optional[StatisticsAnalyzer] = None
        self.distribution_analyzer: Optional[DistributionAnalyzer] = None
        self.outlier_detector: Optional[OutlierDetector] = None
        self.correlation_analyzer: Optional[CorrelationAnalyzer] = None
        self.categorical_analyzer: Optional[CategoricalAnalyzer] = None
        self.trend_analyzer: Optional[TrendAnalyzer] = None
        self.insight_generator: Optional[BusinessInsightGenerator] = None
        
        # Execution tracking
        self.execution_log: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results: Dict[str, Any] = {}
        
    def _log_step(self, step_name: str, status: str, 
                  details: Optional[str] = None) -> None:
        """
        Log a pipeline execution step.
        
        Args:
            step_name: Name of the step.
            status: Status of the step (STARTED, COMPLETED, FAILED).
            details: Optional details about the step.
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step_name,
            'status': status,
            'details': details,
        }
        self.execution_log.append(entry)
        
        if status == 'STARTED':
            logger.info(f"[EDA] Step '{step_name}' started")
        elif status == 'COMPLETED':
            logger.info(f"[EDA] Step '{step_name}' completed" + 
                       (f" - {details}" if details else ""))
        elif status == 'FAILED':
            logger.error(f"[EDA] Step '{step_name}' failed: {details}")
    
    def step_1_load_data(self) -> pd.DataFrame:
        """
        Step 1: Load cleaned dataset.
        
        Returns:
            pd.DataFrame: Loaded dataset.
        """
        self._log_step('Load Data', 'STARTED', f"File: {self.data_file_path}")
        
        try:
            loader = DataLoader()
            self.df = loader.load(self.data_file_path)
            
            # Convert Date column to datetime if present
            if 'Date' in self.df.columns:
                self.df['Date'] = pd.to_datetime(self.df['Date'], errors='coerce')
            
            self._log_step('Load Data', 'COMPLETED', 
                          f"Loaded {len(self.df)} rows, {len(self.df.columns)} columns")
            return self.df
            
        except Exception as e:
            self._log_step('Load Data', 'FAILED', str(e))
            raise EDAPipelineError(f"Data loading failed: {str(e)}") from e
    
    def step_2_profile_dataset(self) -> Dict[str, Any]:
        """
        Step 2: Generate dataset profile.
        
        Returns:
            Dict with profile results.
        """
        self._log_step('Dataset Profiling', 'STARTED')
        
        try:
            self.profiler = DatasetProfiler(self.df)
            profile = self.profiler.generate_profile()
            self.profiler.save_profile_report()
            
            self._log_step('Dataset Profiling', 'COMPLETED', 
                          f"Profile saved to reports/eda/dataset_profile.txt")
            return profile
            
        except Exception as e:
            self._log_step('Dataset Profiling', 'FAILED', str(e))
            logger.warning(f"Dataset profiling failed: {str(e)}")
            return {}
    
    def step_3_descriptive_statistics(self) -> Dict[str, Any]:
        """
        Step 3: Calculate descriptive statistics.
        
        Returns:
            Dict with statistics results.
        """
        self._log_step('Descriptive Statistics', 'STARTED')
        
        try:
            self.statistics_analyzer = StatisticsAnalyzer(self.df)
            stats = self.statistics_analyzer.analyze_all()
            self.statistics_analyzer.save_statistics_csv()
            
            self._log_step('Descriptive Statistics', 'COMPLETED',
                          f"Statistics saved to reports/eda/descriptive_statistics.csv")
            return stats
            
        except Exception as e:
            self._log_step('Descriptive Statistics', 'FAILED', str(e))
            logger.warning(f"Descriptive statistics failed: {str(e)}")
            return {}
    
    def step_4_distribution_analysis(self) -> Dict[str, Any]:
        """
        Step 4: Analyze distributions.
        
        Returns:
            Dict with distribution results.
        """
        self._log_step('Distribution Analysis', 'STARTED')
        
        try:
            self.distribution_analyzer = DistributionAnalyzer(self.df)
            distributions = self.distribution_analyzer.analyze_all()
            
            self._log_step('Distribution Analysis', 'COMPLETED',
                          f"Generated {len(distributions)} distribution plots")
            return distributions
            
        except Exception as e:
            self._log_step('Distribution Analysis', 'FAILED', str(e))
            logger.warning(f"Distribution analysis failed: {str(e)}")
            return {}
    
    def step_5_outlier_detection(self) -> Dict[str, Any]:
        """
        Step 5: Detect outliers.
        
        Returns:
            Dict with outlier results.
        """
        self._log_step('Outlier Detection', 'STARTED')
        
        try:
            self.outlier_detector = OutlierDetector(self.df)
            outliers = self.outlier_detector.analyze_all()
            self.outlier_detector.save_outlier_report()
            
            self._log_step('Outlier Detection', 'COMPLETED',
                          f"Outlier report saved to reports/eda/outlier_report.csv")
            return outliers
            
        except Exception as e:
            self._log_step('Outlier Detection', 'FAILED', str(e))
            logger.warning(f"Outlier detection failed: {str(e)}")
            return {}
    
    def step_6_correlation_analysis(self) -> Dict[str, Any]:
        """
        Step 6: Analyze correlations.
        
        Returns:
            Dict with correlation results.
        """
        self._log_step('Correlation Analysis', 'STARTED')
        
        try:
            self.correlation_analyzer = CorrelationAnalyzer(self.df)
            correlations = self.correlation_analyzer.analyze_all()
            self.correlation_analyzer.save_correlation_csv()
            
            self._log_step('Correlation Analysis', 'COMPLETED',
                          f"Correlation matrices saved to reports/eda/")
            return correlations
            
        except Exception as e:
            self._log_step('Correlation Analysis', 'FAILED', str(e))
            logger.warning(f"Correlation analysis failed: {str(e)}")
            return {}
    
    def step_7_categorical_analysis(self) -> Dict[str, Any]:
        """
        Step 7: Analyze categorical data.
        
        Returns:
            Dict with categorical results.
        """
        self._log_step('Categorical Analysis', 'STARTED')
        
        try:
            self.categorical_analyzer = CategoricalAnalyzer(self.df)
            categorical = self.categorical_analyzer.analyze_all()
            self.categorical_analyzer.save_categorical_summary()
            
            self._log_step('Categorical Analysis', 'COMPLETED',
                          f"Categorical summary saved to reports/eda/categorical_summary.csv")
            return categorical
            
        except Exception as e:
            self._log_step('Categorical Analysis', 'FAILED', str(e))
            logger.warning(f"Categorical analysis failed: {str(e)}")
            return {}
    
    def step_8_trend_analysis(self) -> Dict[str, Any]:
        """
        Step 8: Analyze trends.
        
        Returns:
            Dict with trend results.
        """
        self._log_step('Trend Analysis', 'STARTED')
        
        try:
            self.trend_analyzer = TrendAnalyzer(self.df)
            trends = self.trend_analyzer.analyze_all()
            
            self._log_step('Trend Analysis', 'COMPLETED',
                          f"Trend charts saved to visualizations/trends/")
            return trends
            
        except Exception as e:
            self._log_step('Trend Analysis', 'FAILED', str(e))
            logger.warning(f"Trend analysis failed: {str(e)}")
            return {}
    
    def step_9_business_insights(self) -> Dict[str, Any]:
        """
        Step 9: Generate business insights.
        
        Returns:
            Dict with business insights.
        """
        self._log_step('Business Insights', 'STARTED')
        
        try:
            self.insight_generator = BusinessInsightGenerator(self.df)
            insights = self.insight_generator.generate_all_insights()
            self.insight_generator.save_insights_report()
            
            self._log_step('Business Insights', 'COMPLETED',
                          f"Insights report saved to reports/eda/business_insights.txt")
            return insights
            
        except Exception as e:
            self._log_step('Business Insights', 'FAILED', str(e))
            logger.warning(f"Business insights failed: {str(e)}")
            return {}
    
    def step_10_executive_summary(self) -> str:
        """
        Step 10: Generate executive summary report.
        
        Returns:
            str: Executive summary content.
        """
        self._log_step('Executive Summary', 'STARTED')
        
        try:
            summary = self._generate_executive_summary()
            
            output_path = config.REPORTS_DIR / 'eda' / 'executive_summary.txt'
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            self._log_step('Executive Summary', 'COMPLETED',
                          f"Summary saved to reports/eda/executive_summary.txt")
            return summary
            
        except Exception as e:
            self._log_step('Executive Summary', 'FAILED', str(e))
            logger.warning(f"Executive summary failed: {str(e)}")
            return ""
    
    def _generate_executive_summary(self) -> str:
        """
        Generate comprehensive executive summary.
        
        Returns:
            str: Formatted executive summary.
        """
        lines = []
        lines.append("=" * 80)
        lines.append(" " * 25 + "EXECUTIVE SUMMARY REPORT")
        lines.append(" " * 20 + "E-Commerce Data Analysis")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # 1. Dataset Overview
        lines.append("-" * 80)
        lines.append("1. DATASET OVERVIEW")
        lines.append("-" * 80)
        if self.profiler:
            profile = self.profiler.get_profile()
            struct = profile.get('structure', {})
            lines.append(f"  Total Records:    {struct.get('total_rows', 'N/A'):,}")
            lines.append(f"  Total Features:   {struct.get('total_columns', 'N/A')}")
            lines.append(f"  Memory Usage:     {struct.get('memory_usage_mb', 'N/A'):.4f} MB")
        lines.append("")
        
        # 2. Key Findings
        lines.append("-" * 80)
        lines.append("2. KEY FINDINGS")
        lines.append("-" * 80)
        if self.statistics_analyzer:
            stats = self.statistics_analyzer.get_statistics()
            for col, col_stats in stats.items():
                if 'basic' in col_stats:
                    basic = col_stats['basic']
                    lines.append(f"  {col}:")
                    lines.append(f"    Mean: {basic.get('mean', 'N/A')}, Median: {basic.get('median', 'N/A')}, Std: {col_stats.get('dispersion', {}).get('std_deviation', 'N/A')}")
        lines.append("")
        
        # 3. Distribution Classifications
        lines.append("-" * 80)
        lines.append("3. DISTRIBUTION CLASSIFICATIONS")
        lines.append("-" * 80)
        if self.distribution_analyzer:
            dist_summary = self.distribution_analyzer.get_distribution_summary()
            for _, row in dist_summary.iterrows():
                lines.append(f"  {row['Column']:<20} {row['Classification']:<30} (Confidence: {row['Confidence']:.2%})")
        lines.append("")
        
        # 4. Correlation Findings
        lines.append("-" * 80)
        lines.append("4. CORRELATION FINDINGS")
        lines.append("-" * 80)
        if self.correlation_analyzer:
            corr_results = self.correlation_analyzer.get_results()
            pearson = corr_results.get('pearson_correlations', {})
            if pearson.get('strong_positive'):
                lines.append("  Strong Positive Correlations:")
                for corr in pearson['strong_positive'][:5]:
                    lines.append(f"    {corr['column_1']} <-> {corr['column_2']}: {corr['correlation']:.4f}")
            if pearson.get('strong_negative'):
                lines.append("  Strong Negative Correlations:")
                for corr in pearson['strong_negative'][:5]:
                    lines.append(f"    {corr['column_1']} <-> {corr['column_2']}: {corr['correlation']:.4f}")
        lines.append("")
        
        # 5. Major Outliers
        lines.append("-" * 80)
        lines.append("5. MAJOR OUTLIERS")
        lines.append("-" * 80)
        if self.outlier_detector:
            outlier_results = self.outlier_detector.get_results()
            for col, results in outlier_results.items():
                combined = results.get('combined', {})
                if combined.get('outlier_count', 0) > 0:
                    lines.append(f"  {col}: {combined['outlier_count']} outliers ({combined.get('outlier_percentage', 0):.2f}%)")
        lines.append("")
        
        # 6. Business Insights Summary
        lines.append("-" * 80)
        lines.append("6. BUSINESS INSIGHTS SUMMARY")
        lines.append("-" * 80)
        if self.insight_generator:
            insights = self.insight_generator.get_insights()
            
            revenue = insights.get('revenue', {})
            if 'total_revenue' in revenue:
                lines.append(f"  Total Revenue:               ${revenue['total_revenue']:,.2f}")
                lines.append(f"  Average Order Value:         ${revenue['average_order_value']:,.2f}")
            
            customer = insights.get('customer', {})
            if 'total_unique_customers' in customer:
                lines.append(f"  Total Unique Customers:      {customer['total_unique_customers']:,}")
            
            order = insights.get('order', {})
            if 'fulfillment_rate' in order:
                lines.append(f"  Fulfillment Rate:            {order['fulfillment_rate']:.2f}%")
                lines.append(f"  Cancellation Rate:           {order['cancellation_rate']:.2f}%")
        lines.append("")
        
        # 7. Recommendations
        lines.append("-" * 80)
        lines.append("7. BUSINESS RECOMMENDATIONS")
        lines.append("-" * 80)
        lines.append("  1. Focus marketing efforts on highest-performing products and referral channels")
        lines.append("  2. Investigate and reduce cancellation/return rates through improved quality control")
        lines.append("  3. Optimize inventory for high-demand products identified in analysis")
        lines.append("  4. Consider promotions for low-performing products to increase sales velocity")
        lines.append("  5. Analyze customer segments with highest lifetime value for targeted retention")
        lines.append("")
        
        # 8. Data Quality Observations
        lines.append("-" * 80)
        lines.append("8. DATA QUALITY OBSERVATIONS")
        lines.append("-" * 80)
        if self.profiler:
            profile = self.profiler.get_profile()
            missing = profile.get('missing_values', {})
            lines.append(f"  Overall Missing Data:        {missing.get('overall_missing_pct', 0):.2f}%")
            lines.append(f"  Columns with Missing Data:   {len(missing.get('columns_with_missing', []))}")
        lines.append("")
        
        lines.append("=" * 80)
        lines.append("END OF EXECUTIVE SUMMARY")
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the complete EDA pipeline.
        
        Returns:
            Dict with all analysis results.
        """
        self.start_time = datetime.now()
        logger.info("=" * 80)
        logger.info("E-COMMERCE EDA PIPELINE - EXECUTION STARTED")
        logger.info("=" * 80)
        logger.info(f"Start Time: {self.start_time.isoformat()}")
        logger.info(f"Data File: {self.data_file_path}")
        
        try:
            # Step 1: Load Data
            self.step_1_load_data()
            
            # Step 2: Dataset Profiling
            self.step_2_profile_dataset()
            
            # Step 3: Descriptive Statistics
            self.step_3_descriptive_statistics()
            
            # Step 4: Distribution Analysis
            self.step_4_distribution_analysis()
            
            # Step 5: Outlier Detection
            self.step_5_outlier_detection()
            
            # Step 6: Correlation Analysis
            self.step_6_correlation_analysis()
            
            # Step 7: Categorical Analysis
            self.step_7_categorical_analysis()
            
            # Step 8: Trend Analysis
            self.step_8_trend_analysis()
            
            # Step 9: Business Insights
            self.step_9_business_insights()
            
            # Step 10: Executive Summary
            self.step_10_executive_summary()
            
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            logger.info("=" * 80)
            logger.info("E-COMMERCE EDA PIPELINE - EXECUTION COMPLETED")
            logger.info("=" * 80)
            logger.info(f"End Time: {self.end_time.isoformat()}")
            logger.info(f"Duration: {duration:.2f} seconds")
            
            self.results = {
                'status': 'SUCCESS',
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'duration_seconds': duration,
                'rows_analyzed': len(self.df) if self.df is not None else 0,
                'columns_analyzed': len(self.df.columns) if self.df is not None else 0,
                'execution_log': self.execution_log,
            }
            
            return self.results
            
        except EDAPipelineError as e:
            self.end_time = datetime.now()
            logger.critical(f"EDA pipeline failed: {str(e)}")
            raise
        except Exception as e:
            self.end_time = datetime.now()
            logger.critical(f"Unexpected EDA pipeline failure: {str(e)}")
            raise EDAPipelineError(f"Pipeline execution failed: {str(e)}") from e
    
    def get_execution_summary(self) -> str:
        """
        Get human-readable execution summary.
        
        Returns:
            str: Formatted execution summary.
        """
        if not self.execution_log:
            return "EDA Pipeline has not been executed yet."
        
        lines = []
        lines.append("=" * 80)
        lines.append("EDA PIPELINE EXECUTION SUMMARY")
        lines.append("=" * 80)
        
        for entry in self.execution_log:
            timestamp = entry['timestamp'].split('T')[1].split('.')[0]
            status_icon = "OK" if entry['status'] == 'COMPLETED' else \
                         "FAIL" if entry['status'] == 'FAILED' else "RUN"
            lines.append(f"[{timestamp}] {status_icon:<5} {entry['step']:<35} {entry['status']:<12}")
        
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            lines.append("-" * 80)
            lines.append(f"Total Duration: {duration:.2f} seconds")
        
        lines.append("=" * 80)
        return "\n".join(lines)
