import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

from .config import config


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class DataValidator:
    """
    Enterprise-grade data validator enforcing business rules.
    
    Validates data against configurable business rules and applies
    corrections with detailed logging.
    """
    
    def __init__(self):
        """Initialize the validator with tracking."""
        self.validation_stats: Dict[str, int] = {}
        self.validation_errors: List[Dict[str, Any]] = []
        self.correction_log: List[Dict[str, Any]] = []
        
    def _log_validation_error(self, rule: str, column: str, 
                               row_index: int, value: Any, 
                               expected: str, action: str) -> None:
        """
        Log a validation error for audit trail.
        
        Args:
            rule: Rule name that was violated.
            column: Column where violation occurred.
            row_index: Row index of the violation.
            value: Invalid value.
            expected: Expected valid value or condition.
            action: Action taken to resolve.
        """
        self.validation_errors.append({
            'rule': rule,
            'column': column,
            'row_index': row_index,
            'value': str(value) if pd.notna(value) else 'NULL',
            'expected': expected,
            'action': action,
        })
    
    def _log_correction(self, rule: str, column: str, 
                       row_index: int, original: Any, 
                       corrected: Any) -> None:
        """
        Log a correction made during validation.
        
        Args:
            rule: Rule that triggered correction.
            column: Column where correction was made.
            row_index: Row index.
            original: Original value.
            corrected: Corrected value.
        """
        self.correction_log.append({
            'rule': rule,
            'column': column,
            'row_index': row_index,
            'original': str(original) if pd.notna(original) else 'NULL',
            'corrected': str(corrected) if pd.notna(corrected) else 'NULL',
        })
    
    def validate_quantity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rule 1: Validate Quantity > 0
        Flag and correct invalid values.
        
        Args:
            df: DataFrame to validate.
            
        Returns:
            pd.DataFrame: DataFrame with validated quantities.
        """
        if 'Quantity' not in df.columns:
            logger.warning("Column 'Quantity' not found, skipping validation")
            return df.copy()
        
        df_clean = df.copy()
        invalid_mask = df_clean['Quantity'] <= 0
        invalid_count = invalid_mask.sum()
        
        if invalid_count > 0:
            logger.warning(f"Rule 1 (Quantity > 0): {invalid_count} invalid records found")
            
            # Replace invalid quantities with median of valid quantities
            valid_quantities = df_clean.loc[~invalid_mask, 'Quantity']
            median_qty = valid_quantities.median() if len(valid_quantities) > 0 else 1
            
            for idx in df_clean[invalid_mask].index:
                original = df_clean.at[idx, 'Quantity']
                df_clean.at[idx, 'Quantity'] = median_qty
                self._log_validation_error('Rule 1: Quantity > 0', 'Quantity',
                                           idx, original, 'Value > 0', 
                                           f'Replaced with median ({median_qty})')
                self._log_correction('quantity_validation', 'Quantity', idx,
                                   original, median_qty)
            
            logger.info(f"Rule 1: Corrected {invalid_count} invalid quantities with median ({median_qty})")
        else:
            logger.info("Rule 1 (Quantity > 0): All records valid")
        
        self.validation_stats['quantity_invalid'] = int(invalid_count)
        return df_clean
    
    def validate_unit_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rule 2: Validate UnitPrice > 0
        Flag and correct invalid values.
        
        Args:
            df: DataFrame to validate.
            
        Returns:
            pd.DataFrame: DataFrame with validated unit prices.
        """
        if 'UnitPrice' not in df.columns:
            logger.warning("Column 'UnitPrice' not found, skipping validation")
            return df.copy()
        
        df_clean = df.copy()
        invalid_mask = df_clean['UnitPrice'] <= 0
        invalid_count = invalid_mask.sum()
        
        if invalid_count > 0:
            logger.warning(f"Rule 2 (UnitPrice > 0): {invalid_count} invalid records found")
            
            # Replace invalid prices with median of valid prices
            valid_prices = df_clean.loc[~invalid_mask, 'UnitPrice']
            median_price = valid_prices.median() if len(valid_prices) > 0 else 1.0
            
            for idx in df_clean[invalid_mask].index:
                original = df_clean.at[idx, 'UnitPrice']
                df_clean.at[idx, 'UnitPrice'] = median_price
                self._log_validation_error('Rule 2: UnitPrice > 0', 'UnitPrice',
                                           idx, original, 'Value > 0',
                                           f'Replaced with median ({median_price})')
                self._log_correction('unit_price_validation', 'UnitPrice', idx,
                                   original, median_price)
            
            logger.info(f"Rule 2: Corrected {invalid_count} invalid unit prices with median ({median_price})")
        else:
            logger.info("Rule 2 (UnitPrice > 0): All records valid")
        
        self.validation_stats['unit_price_invalid'] = int(invalid_count)
        return df_clean
    
    def validate_items_in_cart(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rule 3: Validate ItemsInCart >= Quantity
        Flag inconsistencies and correct.
        
        Args:
            df: DataFrame to validate.
            
        Returns:
            pd.DataFrame: DataFrame with validated items in cart.
        """
        if 'ItemsInCart' not in df.columns or 'Quantity' not in df.columns:
            logger.warning("Columns 'ItemsInCart' or 'Quantity' not found, skipping validation")
            return df.copy()
        
        df_clean = df.copy()
        
        # Handle missing values first
        valid_mask = df_clean['ItemsInCart'].notna() & df_clean['Quantity'].notna()
        inconsistent_mask = valid_mask & (df_clean['ItemsInCart'] < df_clean['Quantity'])
        inconsistent_count = inconsistent_mask.sum()
        
        if inconsistent_count > 0:
            logger.warning(f"Rule 3 (ItemsInCart >= Quantity): {inconsistent_count} inconsistent records found")
            
            for idx in df_clean[inconsistent_mask].index:
                original = df_clean.at[idx, 'ItemsInCart']
                quantity = df_clean.at[idx, 'Quantity']
                corrected = quantity  # Set ItemsInCart = Quantity
                
                df_clean.at[idx, 'ItemsInCart'] = corrected
                self._log_validation_error('Rule 3: ItemsInCart >= Quantity', 
                                           'ItemsInCart', idx, original,
                                           f'Value >= {quantity}',
                                           f'Replaced with Quantity ({quantity})')
                self._log_correction('items_in_cart_validation', 'ItemsInCart', idx,
                                   original, corrected)
            
            logger.info(f"Rule 3: Corrected {inconsistent_count} inconsistent ItemsInCart values")
        else:
            logger.info("Rule 3 (ItemsInCart >= Quantity): All records valid")
        
        self.validation_stats['items_in_cart_inconsistent'] = int(inconsistent_count)
        return df_clean
    
    def validate_total_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rule 4: Validate TotalPrice = Quantity * UnitPrice
        If mismatch, correct TotalPrice and store correction log.
        
        Args:
            df: DataFrame to validate.
            
        Returns:
            pd.DataFrame: DataFrame with validated total prices.
        """
        required_cols = ['TotalPrice', 'Quantity', 'UnitPrice']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            logger.warning(f"Missing columns {missing_cols}, skipping TotalPrice validation")
            return df.copy()
        
        df_clean = df.copy()
        
        # Calculate expected TotalPrice
        expected_total = df_clean['Quantity'] * df_clean['UnitPrice']
        
        # Find mismatches (with tolerance for floating point)
        tolerance = 0.01
        valid_mask = (df_clean['TotalPrice'].notna() & 
                     df_clean['Quantity'].notna() & 
                     df_clean['UnitPrice'].notna())
        
        mismatch_mask = valid_mask & (abs(df_clean['TotalPrice'] - expected_total) > tolerance)
        mismatch_count = mismatch_mask.sum()
        
        if mismatch_count > 0:
            logger.warning(f"Rule 4 (TotalPrice = Qty * UnitPrice): {mismatch_count} mismatched records found")
            
            for idx in df_clean[mismatch_mask].index:
                original = df_clean.at[idx, 'TotalPrice']
                expected = round(expected_total.at[idx], 2)
                
                df_clean.at[idx, 'TotalPrice'] = expected
                self._log_validation_error('Rule 4: TotalPrice = Qty * UnitPrice',
                                           'TotalPrice', idx, original,
                                           f'Expected: {expected}',
                                           f'Corrected to {expected}')
                self._log_correction('total_price_validation', 'TotalPrice', idx,
                                   original, expected)
            
            logger.info(f"Rule 4: Corrected {mismatch_count} TotalPrice mismatches")
        else:
            logger.info("Rule 4 (TotalPrice = Qty * UnitPrice): All records valid")
        
        # Fill any remaining NaN TotalPrice values
        nan_total = df_clean['TotalPrice'].isna()
        nan_count = nan_total.sum()
        
        if nan_count > 0:
            for idx in df_clean[nan_total].index:
                if pd.notna(df_clean.at[idx, 'Quantity']) and pd.notna(df_clean.at[idx, 'UnitPrice']):
                    calculated = round(df_clean.at[idx, 'Quantity'] * df_clean.at[idx, 'UnitPrice'], 2)
                    df_clean.at[idx, 'TotalPrice'] = calculated
                    self._log_correction('total_price_calculation', 'TotalPrice', idx,
                                       'NaN', calculated)
            
            logger.info(f"Rule 4: Calculated {nan_count} missing TotalPrice values")
        
        self.validation_stats['total_price_mismatched'] = int(mismatch_count)
        self.validation_stats['total_price_calculated'] = int(nan_count)
        return df_clean
    
    def validate_order_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rule 5: Standardize OrderStatus to allowed values.
        
        Args:
            df: DataFrame to validate.
            
        Returns:
            pd.DataFrame: DataFrame with standardized order statuses.
        """
        if 'OrderStatus' not in df.columns:
            logger.warning("Column 'OrderStatus' not found, skipping validation")
            return df.copy()
        
        df_clean = df.copy()
        invalid_count = 0
        
        for idx, value in df_clean['OrderStatus'].items():
            if pd.isna(value) or str(value).strip() == '':
                continue
            
            original = str(value).strip()
            
            # Check if already valid
            if original in config.VALID_ORDER_STATUSES:
                continue
            
            # Try mapping
            standardized = config.ORDER_STATUS_MAPPING.get(original, original)
            
            # If still not valid, try title case
            if standardized not in config.VALID_ORDER_STATUSES:
                standardized = original.title()
            
            # If still not valid, flag as invalid
            if standardized not in config.VALID_ORDER_STATUSES:
                invalid_count += 1
                self._log_validation_error('Rule 5: OrderStatus standardization',
                                           'OrderStatus', idx, original,
                                           f'One of: {config.VALID_ORDER_STATUSES}',
                                           'Flagged as invalid - no mapping found')
            else:
                if standardized != original:
                    df_clean.at[idx, 'OrderStatus'] = standardized
                    self._log_correction('order_status_standardization', 'OrderStatus',
                                       idx, original, standardized)
        
        if invalid_count > 0:
            logger.warning(f"Rule 5: {invalid_count} OrderStatus values could not be standardized")
        else:
            logger.info("Rule 5 (OrderStatus): All values standardized successfully")
        
        self.validation_stats['order_status_invalid'] = invalid_count
        return df_clean
    
    def validate_payment_method(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Rule 6: Standardize PaymentMethod values.
        
        Args:
            df: DataFrame to validate.
            
        Returns:
            pd.DataFrame: DataFrame with standardized payment methods.
        """
        if 'PaymentMethod' not in df.columns:
            logger.warning("Column 'PaymentMethod' not found, skipping validation")
            return df.copy()
        
        df_clean = df.copy()
        invalid_count = 0
        
        for idx, value in df_clean['PaymentMethod'].items():
            if pd.isna(value) or str(value).strip() == '':
                continue
            
            original = str(value).strip()
            standardized = config.PAYMENT_METHOD_MAPPING.get(original, original)
            
            if standardized != original:
                df_clean.at[idx, 'PaymentMethod'] = standardized
                self._log_correction('payment_method_standardization', 'PaymentMethod',
                                   idx, original, standardized)
            else:
                # Check if it's already a valid standard form
                valid_methods = set(config.PAYMENT_METHOD_MAPPING.values())
                if original not in valid_methods:
                    invalid_count += 1
                    self._log_validation_error('Rule 6: PaymentMethod standardization',
                                               'PaymentMethod', idx, original,
                                               'Standardized payment method',
                                               'Flagged as unmapped')
        
        if invalid_count > 0:
            logger.warning(f"Rule 6: {invalid_count} PaymentMethod values could not be standardized")
        else:
            logger.info("Rule 6 (PaymentMethod): All values standardized successfully")
        
        self.validation_stats['payment_method_invalid'] = invalid_count
        return df_clean
    
    def run_all_validations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run all business validation rules in sequence.
        
        Args:
            df: DataFrame to validate.
            
        Returns:
            pd.DataFrame: Validated DataFrame.
        """
        logger.info("=" * 60)
        logger.info("STARTING BUSINESS DATA VALIDATION")
        logger.info("=" * 60)
        
        df_clean = df.copy()
        
        # Rule 1: Quantity > 0
        df_clean = self.validate_quantity(df_clean)
        
        # Rule 2: UnitPrice > 0
        df_clean = self.validate_unit_price(df_clean)
        
        # Rule 3: ItemsInCart >= Quantity
        df_clean = self.validate_items_in_cart(df_clean)
        
        # Rule 4: TotalPrice = Quantity * UnitPrice
        df_clean = self.validate_total_price(df_clean)
        
        # Rule 5: OrderStatus standardization
        df_clean = self.validate_order_status(df_clean)
        
        # Rule 6: PaymentMethod standardization
        df_clean = self.validate_payment_method(df_clean)
        
        logger.info("=" * 60)
        logger.info("BUSINESS DATA VALIDATION COMPLETED")
        logger.info("=" * 60)
        
        total_issues = sum(self.validation_stats.values())
        logger.info(f"Total validation issues found and corrected: {total_issues}")
        
        return df_clean
    
    def get_validation_stats(self) -> Dict[str, int]:
        """Get validation statistics."""
        return self.validation_stats.copy()
    
    def get_validation_errors(self) -> List[Dict[str, Any]]:
        """Get validation errors log."""
        return self.validation_errors.copy()
    
    def get_correction_log(self) -> List[Dict[str, Any]]:
        """Get correction log."""
        return self.correction_log.copy()