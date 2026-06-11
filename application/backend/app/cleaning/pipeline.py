import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd

from .config import config
from .data_loader import DataLoader, DataLoadError, FileValidationError
from .cleaner import DataCleaner, DataCleaningError
from .validator import DataValidator, ValidationError
from .reporter import DataQualityReporter


logger = logging.getLogger(__name__)


class PipelineExecutionError(Exception):
    """Custom exception for pipeline execution errors."""
    pass


class DataCleaningPipeline:
    """
    Enterprise-grade data cleaning pipeline orchestrator.
    
    Coordinates all cleaning operations in a defined sequence with
    comprehensive logging, error handling, and reporting.
    """
    
    def __init__(self, 
                 raw_file_path: Optional[Path] = None,
                 output_file_path: Optional[Path] = None):
        """
        Initialize the pipeline.
        
        Args:
            raw_file_path: Path to raw data file. Uses config default if not provided.
            output_file_path: Path for cleaned output. Uses config default if not provided.
        """
        self.raw_file_path = raw_file_path or config.RAW_DATA_FILE
        self.output_file_path = output_file_path or config.CLEANED_DATA_FILE
        
        # Initialize components
        self.loader = DataLoader()
        self.cleaner = DataCleaner()
        self.validator = DataValidator()
        self.reporter = DataQualityReporter()
        
        # Data containers
        self.raw_data: Optional[pd.DataFrame] = None
        self.cleaned_data: Optional[pd.DataFrame] = None
        
        # Execution tracking
        self.execution_log: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
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
            logger.info(f"[PIPELINE] Step '{step_name}' started")
        elif status == 'COMPLETED':
            logger.info(f"[PIPELINE] Step '{step_name}' completed" + 
                       (f" - {details}" if details else ""))
        elif status == 'FAILED':
            logger.error(f"[PIPELINE] Step '{step_name}' failed: {details}")
    
    def step_1_load_data(self) -> pd.DataFrame:
        """
        Step 1: Load raw data from file.
        
        Returns:
            pd.DataFrame: Loaded raw data.
            
        Raises:
            PipelineExecutionError: If data loading fails.
        """
        self._log_step('Load Data', 'STARTED', f"File: {self.raw_file_path}")
        
        try:
            self.raw_data = self.loader.load(self.raw_file_path)
            self._log_step('Load Data', 'COMPLETED', 
                          f"Loaded {len(self.raw_data)} rows, {len(self.raw_data.columns)} columns")
            return self.raw_data
            
        except (DataLoadError, FileValidationError) as e:
            self._log_step('Load Data', 'FAILED', str(e))
            raise PipelineExecutionError(f"Data loading failed: {str(e)}") from e
        except Exception as e:
            self._log_step('Load Data', 'FAILED', f"Unexpected error: {str(e)}")
            raise PipelineExecutionError(f"Unexpected error during data loading: {str(e)}") from e
    
    def step_2_initial_assessment(self) -> str:
        """
        Step 2: Generate initial data quality assessment report.
        
        Returns:
            str: Quality report content.
        """
        self._log_step('Initial Assessment', 'STARTED')
        
        try:
            report = self.reporter.generate_data_quality_report(self.raw_data)
            self._log_step('Initial Assessment', 'COMPLETED', 
                          f"Report saved to {config.QUALITY_REPORT_FILE}")
            return report
            
        except Exception as e:
            self._log_step('Initial Assessment', 'FAILED', str(e))
            logger.warning(f"Initial assessment failed: {str(e)}, continuing pipeline")
            return ""
    
    def step_3_handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 3: Detect and handle missing values.
        
        Args:
            df: DataFrame to clean.
            
        Returns:
            pd.DataFrame: DataFrame with missing values handled.
        """
        self._log_step('Missing Value Handling', 'STARTED')
        
        try:
            # First detect missing values
            missing_counts = self.cleaner.detect_missing_values(df)
            total_missing = sum(missing_counts.values())
            
            # Then handle them
            df_clean = self.cleaner.handle_missing_values(df)
            
            self._log_step('Missing Value Handling', 'COMPLETED',
                          f"Detected {total_missing} missing values, fixed {self.cleaner.cleaning_stats.get('missing_values_fixed', 0)}")
            return df_clean
            
        except Exception as e:
            self._log_step('Missing Value Handling', 'FAILED', str(e))
            logger.warning(f"Missing value handling failed: {str(e)}, continuing with original data")
            return df.copy()
    
    def step_4_remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 4: Detect and remove duplicate records.
        
        Args:
            df: DataFrame to clean.
            
        Returns:
            pd.DataFrame: DataFrame with duplicates removed.
        """
        self._log_step('Duplicate Removal', 'STARTED')
        
        try:
            initial_count = len(df)
            df_clean = self.cleaner.remove_duplicates(df)
            removed = initial_count - len(df_clean)
            
            self._log_step('Duplicate Removal', 'COMPLETED',
                          f"Removed {removed} duplicate records ({initial_count} -> {len(df_clean)} rows)")
            return df_clean
            
        except Exception as e:
            self._log_step('Duplicate Removal', 'FAILED', str(e))
            logger.warning(f"Duplicate removal failed: {str(e)}, continuing with original data")
            return df.copy()
    
    def step_5_correct_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 5: Correct data types and formats.
        
        Args:
            df: DataFrame to clean.
            
        Returns:
            pd.DataFrame: DataFrame with corrected data types.
        """
        self._log_step('Data Type Correction', 'STARTED')
        
        try:
            df_clean = self.cleaner.correct_data_types(df)
            
            corrections = (self.cleaner.cleaning_stats.get('invalid_dates_corrected', 0) +
                          self.cleaner.cleaning_stats.get('numeric_format_cleaning_corrections', 0))
            
            self._log_step('Data Type Correction', 'COMPLETED',
                          f"Applied data type corrections (dates, numeric formats, text)")
            return df_clean
            
        except Exception as e:
            self._log_step('Data Type Correction', 'FAILED', str(e))
            logger.warning(f"Data type correction failed: {str(e)}, continuing with original data")
            return df.copy()
    
    def step_6_standardize_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 6: Standardize text values using business mappings.
        
        Args:
            df: DataFrame to clean.
            
        Returns:
            pd.DataFrame: DataFrame with standardized text values.
        """
        self._log_step('Text Standardization', 'STARTED')
        
        try:
            df_clean = self.cleaner.standardize_text_values(df)
            
            total_std = (self.cleaner.cleaning_stats.get('order_status_standardized', 0) +
                        self.cleaner.cleaning_stats.get('payment_method_standardized', 0) +
                        self.cleaner.cleaning_stats.get('referral_source_standardized', 0))
            
            self._log_step('Text Standardization', 'COMPLETED',
                          f"Standardized {total_std} text values")
            return df_clean
            
        except Exception as e:
            self._log_step('Text Standardization', 'FAILED', str(e))
            logger.warning(f"Text standardization failed: {str(e)}, continuing with original data")
            return df.copy()
    
    def step_7_validate_business_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Step 7: Apply business validation rules.
        
        Args:
            df: DataFrame to validate.
            
        Returns:
            pd.DataFrame: Validated DataFrame.
        """
        self._log_step('Business Validation', 'STARTED')
        
        try:
            df_clean = self.validator.run_all_validations(df)
            
            total_issues = sum(self.validator.validation_stats.values())
            self._log_step('Business Validation', 'COMPLETED',
                          f"Validated and corrected {total_issues} business rule violations")
            return df_clean
            
        except Exception as e:
            self._log_step('Business Validation', 'FAILED', str(e))
            logger.warning(f"Business validation failed: {str(e)}, continuing with original data")
            return df.copy()
    
    def step_8_generate_reports(self, df_clean: pd.DataFrame) -> Tuple[str, str]:
        """
        Step 8: Generate final quality and cleaning summary reports.
        
        Args:
            df_clean: Cleaned DataFrame.
            
        Returns:
            Tuple[str, str]: Quality report and cleaning summary content.
        """
        self._log_step('Report Generation', 'STARTED')
        
        try:
            # Combine all cleaning stats
            all_stats = {}
            all_stats.update(self.cleaner.cleaning_stats)
            all_stats.update(self.validator.validation_stats)
            
            # Generate cleaning summary
            cleaning_summary = self.reporter.generate_cleaning_summary(
                self.raw_data, df_clean, all_stats
            )
            
            self._log_step('Report Generation', 'COMPLETED',
                          f"Reports saved to {config.REPORTS_DIR}")
            return "", cleaning_summary
            
        except Exception as e:
            self._log_step('Report Generation', 'FAILED', str(e))
            logger.warning(f"Report generation failed: {str(e)}")
            return "", ""
    
    def step_9_save_clean_data(self, df_clean: pd.DataFrame) -> Path:
        """
        Step 9: Save cleaned dataset to output file.
        
        Args:
            df_clean: Cleaned DataFrame to save.
            
        Returns:
            Path: Path to saved file.
        """
        self._log_step('Save Clean Data', 'STARTED', f"Output: {self.output_file_path}")
        
        try:
            # Ensure output directory exists
            self.output_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Preserve original column order
            if self.raw_data is not None:
                original_columns = [col for col in self.raw_data.columns if col in df_clean.columns]
                df_clean = df_clean[original_columns]
            
            # Save with UTF-8 encoding, no index
            df_clean.to_csv(self.output_file_path, 
                           index=False, 
                           encoding=config.ENCODING)
            
            self._log_step('Save Clean Data', 'COMPLETED',
                          f"Saved {len(df_clean)} rows to {self.output_file_path}")
            return self.output_file_path
            
        except Exception as e:
            self._log_step('Save Clean Data', 'FAILED', str(e))
            raise PipelineExecutionError(f"Failed to save cleaned data: {str(e)}") from e
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the complete data cleaning pipeline.
        
        This is the main entry point that orchestrates all cleaning steps
        in the correct sequence with comprehensive error handling.
        
        Returns:
            Dict[str, Any]: Pipeline execution results and statistics.
            
        Raises:
            PipelineExecutionError: If pipeline execution fails critically.
        """
        self.start_time = datetime.now()
        logger.info("=" * 80)
        logger.info("E-COMMERCE DATA CLEANING PIPELINE - EXECUTION STARTED")
        logger.info("=" * 80)
        logger.info(f"Start Time: {self.start_time.isoformat()}")
        logger.info(f"Raw Data: {self.raw_file_path}")
        logger.info(f"Output: {self.output_file_path}")
        
        try:
            # Step 1: Load Data
            df = self.step_1_load_data()
            
            # Step 2: Initial Assessment
            self.step_2_initial_assessment()
            
            # Step 3: Handle Missing Values
            df = self.step_3_handle_missing_values(df)
            
            # Step 4: Remove Duplicates
            df = self.step_4_remove_duplicates(df)
            
            # Step 5: Correct Data Types
            df = self.step_5_correct_data_types(df)
            
            # Step 6: Standardize Text
            df = self.step_6_standardize_text(df)
            
            # Step 7: Validate Business Rules
            df = self.step_7_validate_business_rules(df)
            
            # Store cleaned data
            self.cleaned_data = df.copy()
            
            # Step 8: Generate Reports
            self.step_8_generate_reports(df)
            
            # Step 9: Save Clean Data
            output_path = self.step_9_save_clean_data(df)
            
            self.end_time = datetime.now()
            duration = (self.end_time - self.start_time).total_seconds()
            
            logger.info("=" * 80)
            logger.info("E-COMMERCE DATA CLEANING PIPELINE - EXECUTION COMPLETED")
            logger.info("=" * 80)
            logger.info(f"End Time: {self.end_time.isoformat()}")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Output File: {output_path}")
            
            # Compile results
            results = {
                'status': 'SUCCESS',
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'duration_seconds': duration,
                'raw_rows': len(self.raw_data) if self.raw_data is not None else 0,
                'cleaned_rows': len(self.cleaned_data) if self.cleaned_data is not None else 0,
                'rows_removed': (len(self.raw_data) - len(self.cleaned_data)) if self.raw_data is not None else 0,
                'output_file': str(output_path),
                'cleaning_stats': self.cleaner.get_cleaning_stats(),
                'validation_stats': self.validator.get_validation_stats(),
                'execution_log': self.execution_log,
            }
            
            return results
            
        except PipelineExecutionError as e:
            self.end_time = datetime.now()
            logger.critical(f"Pipeline execution failed: {str(e)}")
            raise
        except Exception as e:
            self.end_time = datetime.now()
            logger.critical(f"Unexpected pipeline failure: {str(e)}")
            raise PipelineExecutionError(f"Pipeline execution failed: {str(e)}") from e
    
    def get_execution_summary(self) -> str:
        """
        Get a human-readable execution summary.
        
        Returns:
            str: Formatted execution summary.
        """
        if not self.execution_log:
            return "Pipeline has not been executed yet."
        
        lines = []
        lines.append("=" * 80)
        lines.append("PIPELINE EXECUTION SUMMARY")
        lines.append("=" * 80)
        
        for entry in self.execution_log:
            timestamp = entry['timestamp'].split('T')[1].split('.')[0]
            status_icon = "✅" if entry['status'] == 'COMPLETED' else \
                         "❌" if entry['status'] == 'FAILED' else "⏳"
            lines.append(f"[{timestamp}] {status_icon} {entry['step']:<30} {entry['status']:<12} {entry.get('details', '')}")
        
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            lines.append("-" * 80)
            lines.append(f"Total Duration: {duration:.2f} seconds")
        
        lines.append("=" * 80)
        return "\n".join(lines)