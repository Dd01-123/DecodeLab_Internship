import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import pandas as pd
import numpy as np

from .config import config


logger = logging.getLogger(__name__)


class DataCleaningError(Exception):
    """Custom exception for data cleaning errors."""
    pass


class DataCleaner:
    """
    Enterprise-grade data cleaner with comprehensive cleaning operations.
    
    Handles missing values, duplicates, data type corrections, and
    text standardization following configurable business rules.
    """
    
    def __init__(self):
        """Initialize the data cleaner with tracking dictionaries."""
        self.cleaning_stats: Dict[str, int] = {}
        self.correction_log: List[Dict[str, Any]] = []
        
    def _log_correction(self, operation: str, column: str, 
                       original: Any, corrected: Any, 
                       row_index: Optional[int] = None) -> None:
        """
        Log a data correction for audit trail.
        
        Args:
            operation: Type of correction performed.
            column: Column name where correction was made.
            original: Original value before correction.
            corrected: Corrected value after operation.
            row_index: Optional row index for traceability.
        """
        self.correction_log.append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'column': column,
            'original': str(original) if pd.notna(original) else 'NULL',
            'corrected': str(corrected) if pd.notna(corrected) else 'NULL',
            'row_index': row_index,
        })
        
        # Update stats
        stat_key = f"{operation}_corrections"
        self.cleaning_stats[stat_key] = self.cleaning_stats.get(stat_key, 0) + 1
    
    def detect_missing_values(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Detect all forms of missing values including NaN, null strings,
        whitespace-only values, and configured missing indicators.
        
        Args:
            df: DataFrame to analyze.
            
        Returns:
            Dict[str, int]: Count of missing values per column.
        """
        missing_counts = {}
        
        for col in df.columns:
            # Standard NaN/Null
            nan_count = df[col].isna().sum()
            
            # String-based missing indicators
            string_missing = 0
            if df[col].dtype == 'object':
                # Check for missing indicators (case-insensitive)
                str_values = df[col].astype(str).str.strip().str.lower()
                indicator_mask = str_values.isin(
                    [indicator.lower() for indicator in config.MISSING_INDICATORS]
                )
                
                # Check for empty/whitespace-only strings
                empty_mask = str_values.eq('')
                
                string_missing = int((indicator_mask | empty_mask).sum())
            
            total_missing = int(nan_count + string_missing)
            missing_counts[col] = total_missing
            
            if total_missing > 0:
                logger.info(f"Column '{col}': {total_missing} missing values detected")
        
        total_missing_all = sum(missing_counts.values())
        logger.info(f"Total missing values detected across all columns: {total_missing_all}")
        return missing_counts
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values according to business rules:
        - Numeric columns: Fill with median
        - Categorical columns: Fill with mode
        - TrackingNumber: Keep as missing (business rule)
        
        Args:
            df: DataFrame to clean.
            
        Returns:
            pd.DataFrame: DataFrame with missing values handled.
        """
        df_clean = df.copy()
        total_fixed = 0
        
        for col in df_clean.columns:
            if col == 'TrackingNumber':
                # Business rule: Keep missing TrackingNumbers as-is
                # They may be genuinely unavailable
                missing_count = df_clean[col].isna().sum()
                if missing_count > 0:
                    logger.info(f"Column '{col}': {missing_count} missing values kept (business rule)")
                continue
            
            # Detect missing values in this column
            missing_mask = df_clean[col].isna()
            
            # Also detect string-based missing indicators
            if df_clean[col].dtype == 'object':
                str_values = df_clean[col].astype(str).str.strip().str.lower()
                indicator_mask = str_values.isin(
                    [indicator.lower() for indicator in config.MISSING_INDICATORS]
                )
                empty_mask = str_values.eq('')
                missing_mask = missing_mask | indicator_mask | empty_mask
            
            missing_count = missing_mask.sum()
            
            if missing_count == 0:
                continue
            
            if col in config.NUMERIC_COLUMNS:
                # Numeric columns: Fill with median
                try:
                    # Convert to numeric first if needed
                    numeric_series = pd.to_numeric(df_clean[col], errors='coerce')
                    median_value = numeric_series.median()
                    
                    if pd.notna(median_value):
                        df_clean.loc[missing_mask, col] = median_value
                        self._log_correction('missing_value_fill_median', col, 
                                           'MISSING', median_value)
                        logger.info(f"Column '{col}': Filled {missing_count} missing values with median ({median_value})")
                        total_fixed += missing_count
                    else:
                        logger.warning(f"Column '{col}': Could not calculate median, skipping")
                except Exception as e:
                    logger.error(f"Column '{col}': Error filling missing values: {str(e)}")
                    
            elif col in config.CATEGORICAL_COLUMNS:
                # Categorical columns: Fill with mode
                try:
                    # Get non-missing values
                    valid_values = df_clean.loc[~missing_mask, col]
                    
                    if len(valid_values) > 0:
                        mode_value = valid_values.mode()
                        if len(mode_value) > 0:
                            fill_value = mode_value.iloc[0]
                            df_clean.loc[missing_mask, col] = fill_value
                            self._log_correction('missing_value_fill_mode', col,
                                               'MISSING', fill_value)
                            logger.info(f"Column '{col}': Filled {missing_count} missing values with mode ('{fill_value}')")
                            total_fixed += missing_count
                except Exception as e:
                    logger.error(f"Column '{col}': Error filling missing values: {str(e)}")
            else:
                # Other columns: Fill with empty string for text, or most common value
                try:
                    if df_clean[col].dtype == 'object':
                        df_clean.loc[missing_mask, col] = ''
                        self._log_correction('missing_value_fill_empty', col,
                                           'MISSING', '')
                        logger.info(f"Column '{col}': Filled {missing_count} missing values with empty string")
                        total_fixed += missing_count
                except Exception as e:
                    logger.error(f"Column '{col}': Error filling missing values: {str(e)}")
        
        self.cleaning_stats['missing_values_fixed'] = total_fixed
        logger.info(f"Total missing values fixed: {total_fixed}")
        return df_clean
    
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove exact duplicate rows from the dataset.
        
        Args:
            df: DataFrame to clean.
            
        Returns:
            pd.DataFrame: DataFrame with duplicates removed.
        """
        initial_count = len(df)
        
        # Identify duplicates (keep=False marks all duplicates)
        duplicate_mask = df.duplicated(keep=False)
        duplicate_count = duplicate_mask.sum()
        unique_duplicates = df.duplicated().sum()
        
        if unique_duplicates == 0:
            logger.info("No duplicate records found")
            self.cleaning_stats['duplicates_removed'] = 0
            return df.copy()
        
        # Remove duplicates (keep='first' keeps the first occurrence)
        df_clean = df.drop_duplicates(keep='first').reset_index(drop=True)
        removed_count = initial_count - len(df_clean)
        
        self.cleaning_stats['duplicates_found'] = int(duplicate_count)
        self.cleaning_stats['duplicates_removed'] = int(removed_count)
        
        logger.info(f"Duplicate analysis: {duplicate_count} duplicate rows found ({unique_duplicates} unique duplicate records)")
        logger.info(f"Removed {removed_count} duplicate records. Rows: {initial_count} -> {len(df_clean)}")
        
        return df_clean
    
    def clean_numeric_column(self, series: pd.Series, 
                             column_name: str) -> pd.Series:
        """
        Clean numeric column by removing currency symbols, commas, spaces,
        and handling text contamination.
        
        Args:
            series: Series to clean.
            column_name: Name of the column for logging.
            
        Returns:
            pd.Series: Cleaned numeric series.
        """
        cleaned = series.copy()
        corrections = 0
        
        if cleaned.dtype == 'object':
            # Convert to string for processing
            cleaned = cleaned.astype(str)
            
            # Remove currency symbols (₹, $, €, £, ¥, etc.)
            cleaned = cleaned.str.replace(r'[₹$€£¥¢]', '', regex=True)
            
            # Remove commas (thousand separators)
            cleaned = cleaned.str.replace(',', '', regex=False)
            
            # Remove spaces
            cleaned = cleaned.str.replace(' ', '', regex=False)
            
            # Remove any remaining non-numeric characters (except decimal point and minus)
            cleaned = cleaned.str.replace(r'[^0-9.\-]', '', regex=True)
            
            # Handle empty strings after cleaning
            cleaned = cleaned.replace('', np.nan)
            
            # Convert to numeric
            cleaned = pd.to_numeric(cleaned, errors='coerce')
            
            # Count corrections (values that changed)
            original_numeric = pd.to_numeric(series, errors='coerce')
            corrections = (cleaned != original_numeric).sum()
            
            if corrections > 0:
                self._log_correction('numeric_format_cleaning', column_name,
                                   'VARIOUS', 'NUMERIC')
                logger.info(f"Column '{column_name}': Cleaned {corrections} values (currency symbols, commas, spaces removed)")
        
        return cleaned
    
    def correct_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Correct data types for all columns:
        - Date: Convert to datetime
        - Numeric: Clean and convert to appropriate numeric type
        - Text: Strip spaces, normalize
        
        Args:
            df: DataFrame to clean.
            
        Returns:
            pd.DataFrame: DataFrame with corrected data types.
        """
        df_clean = df.copy()
        
        # 1. Convert Date column to datetime
        if 'Date' in df_clean.columns:
            logger.info("Converting 'Date' column to datetime format")
            original_dates = df_clean['Date'].copy()
            
            # First, clean string-based missing indicators
            df_clean['Date'] = df_clean['Date'].replace(
                list(config.MISSING_INDICATORS), np.nan
            )
            
            # Convert to datetime
            df_clean['Date'] = pd.to_datetime(df_clean['Date'], 
                                                errors='coerce',
                                                format=config.DATE_FORMAT)
            
            # Count invalid dates
            invalid_dates = df_clean['Date'].isna().sum() - original_dates.isna().sum()
            if invalid_dates > 0:
                self._log_correction('invalid_date_conversion', 'Date',
                                   'INVALID_DATE', 'NaT')
                logger.warning(f"Column 'Date': {invalid_dates} invalid date values detected and set to NaT")
            
            self.cleaning_stats['invalid_dates_corrected'] = int(max(0, invalid_dates))
            logger.info(f"Column 'Date': Converted to datetime. Invalid dates: {invalid_dates}")
        
        # 2. Convert numeric columns
        for col in config.NUMERIC_COLUMNS:
            if col in df_clean.columns:
                logger.info(f"Converting '{col}' to numeric format")
                original_values = df_clean[col].copy()
                df_clean[col] = self.clean_numeric_column(df_clean[col], col)
                
                # Ensure proper numeric type
                if df_clean[col].notna().all() and (df_clean[col] % 1 == 0).all():
                    df_clean[col] = df_clean[col].astype('int64')
                else:
                    df_clean[col] = df_clean[col].astype('float64')
        
        # 3. Clean text columns
        for col in config.TEXT_COLUMNS:
            if col in df_clean.columns:
                logger.info(f"Cleaning text column: '{col}'")
                original_values = df_clean[col].copy()
                
                # Convert to string
                df_clean[col] = df_clean[col].astype(str)
                
                # Strip leading and trailing spaces
                df_clean[col] = df_clean[col].str.strip()
                
                # Remove extra spaces (multiple spaces -> single space)
                df_clean[col] = df_clean[col].str.replace(r'\s+', ' ', regex=True)
                
                # Replace missing indicators with empty string or NaN
                df_clean[col] = df_clean[col].replace(
                    [indicator.lower() for indicator in config.MISSING_INDICATORS],
                    ''
                )
                
                # Count changes
                changes = (df_clean[col] != original_values.astype(str).str.strip()).sum()
                if changes > 0:
                    self._log_correction('text_standardization', col,
                                       'VARIOUS', 'CLEANED')
                    logger.info(f"Column '{col}': Standardized {changes} text values")
        
        self.cleaning_stats['data_type_corrections'] = (
            self.cleaning_stats.get('invalid_dates_corrected', 0) +
            self.cleaning_stats.get('numeric_format_cleaning_corrections', 0) +
            self.cleaning_stats.get('text_standardization_corrections', 0)
        )
        
        return df_clean
    
    def standardize_text_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize text values using mapping dictionaries from config.
        
        Args:
            df: DataFrame to clean.
            
        Returns:
            pd.DataFrame: DataFrame with standardized text values.
        """
        df_clean = df.copy()
        
        # Standardize OrderStatus
        if 'OrderStatus' in df_clean.columns:
            logger.info("Standardizing 'OrderStatus' values")
            corrections = 0
            
            for idx, value in df_clean['OrderStatus'].items():
                if pd.isna(value) or str(value).strip() == '':
                    continue
                
                original = str(value).strip()
                standardized = config.ORDER_STATUS_MAPPING.get(original, original)
                
                # Title case if not in mapping
                if standardized == original and original not in config.VALID_ORDER_STATUSES:
                    standardized = original.title()
                
                if standardized != original:
                    df_clean.at[idx, 'OrderStatus'] = standardized
                    self._log_correction('order_status_standardization', 'OrderStatus',
                                       original, standardized, idx)
                    corrections += 1
            
            self.cleaning_stats['order_status_standardized'] = corrections
            logger.info(f"Column 'OrderStatus': Standardized {corrections} values")
        
        # Standardize PaymentMethod
        if 'PaymentMethod' in df_clean.columns:
            logger.info("Standardizing 'PaymentMethod' values")
            corrections = 0
            
            for idx, value in df_clean['PaymentMethod'].items():
                if pd.isna(value) or str(value).strip() == '':
                    continue
                
                original = str(value).strip()
                standardized = config.PAYMENT_METHOD_MAPPING.get(original, original)
                
                if standardized != original:
                    df_clean.at[idx, 'PaymentMethod'] = standardized
                    self._log_correction('payment_method_standardization', 'PaymentMethod',
                                       original, standardized, idx)
                    corrections += 1
            
            self.cleaning_stats['payment_method_standardized'] = corrections
            logger.info(f"Column 'PaymentMethod': Standardized {corrections} values")
        
        # Standardize ReferralSource (capitalize first letter of each word)
        if 'ReferralSource' in df_clean.columns:
            logger.info("Standardizing 'ReferralSource' values")
            corrections = 0
            
            for idx, value in df_clean['ReferralSource'].items():
                if pd.isna(value) or str(value).strip() == '':
                    continue
                
                original = str(value).strip()
                # Skip if it's a known missing indicator
                if original.lower() in [ind.lower() for ind in config.MISSING_INDICATORS]:
                    continue
                
                standardized = original.title()
                
                if standardized != original:
                    df_clean.at[idx, 'ReferralSource'] = standardized
                    self._log_correction('referral_source_standardization', 'ReferralSource',
                                       original, standardized, idx)
                    corrections += 1
            
            self.cleaning_stats['referral_source_standardized'] = corrections
            logger.info(f"Column 'ReferralSource': Standardized {corrections} values")
        
        return df_clean
    
    def get_cleaning_stats(self) -> Dict[str, int]:
        """Get cleaning statistics."""
        return self.cleaning_stats.copy()
    
    def get_correction_log(self) -> List[Dict[str, Any]]:
        """Get correction log for audit trail."""
        return self.correction_log.copy()