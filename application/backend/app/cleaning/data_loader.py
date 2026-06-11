import logging
import os
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
import pandas as pd

from .config import config


logger = logging.getLogger(__name__)


class DataLoadError(Exception):
    """Custom exception for DataLoader errors."""
    pass

class FileValidationError(Exception):
    """Custom exception for file validation errors."""
    pass


class DataLoader:
    """
    Enterprise-grade data loader with automatic file type detection,
    validation, and comprehensive error handling.
    
    Supports CSV and Excel file formats with configurable options.
    """
    
    SUPPORTED_EXTENSIONS: Dict[str, str] = {
        '.csv': 'csv',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.xlsm': 'excel',
    }
    
    def __init__(self, file_path: Optional[Union[str, Path]] = None):
        """
        Initialize the DataLoader.
        
        Args:
            file_path: Optional path to the data file. Can be set later.
        """
        self.file_path: Optional[Path] = Path(file_path) if file_path else None
        self.file_type: Optional[str] = None
        self.raw_data: Optional[pd.DataFrame] = None
        self.load_metadata: Dict[str, Any] = {}
        
    def _detect_file_type(self, file_path: Path) -> str:
        """
        Automatically detect file type based on extension.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            str: Detected file type ('csv' or 'excel').
            
        Raises:
            FileValidationError: If file type is not supported.
        """
        extension = file_path.suffix.lower()
        
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise FileValidationError(
                f"Unsupported file type: '{extension}'. "
                f"Supported types: {list(self.SUPPORTED_EXTENSIONS.keys())}"
            )
        
        file_type = self.SUPPORTED_EXTENSIONS[extension]
        logger.info(f"Detected file type: {file_type} (extension: {extension})")
        return file_type
    
    def _validate_file_exists(self, file_path: Path) -> None:
        """
        Validate that the file exists and is accessible.
        
        Args:
            file_path: Path to validate.
            
        Raises:
            FileValidationError: If file does not exist or is not accessible.
        """
        if not file_path.exists():
            raise FileValidationError(
                f"File not found: {file_path.absolute()}"
            )
        
        if not file_path.is_file():
            raise FileValidationError(
                f"Path is not a file: {file_path.absolute()}"
            )
        
        if not os.access(file_path, os.R_OK):
            raise FileValidationError(
                f"File is not readable: {file_path.absolute()}"
            )
        
        logger.info(f"File validation passed: {file_path.name}")
    
    def _validate_file_size(self, file_path: Path, 
                           max_size_mb: float = 1000.0) -> None:
        """
        Validate file size is within acceptable limits.
        
        Args:
            file_path: Path to validate.
            max_size_mb: Maximum allowed file size in MB.
            
        Raises:
            FileValidationError: If file exceeds maximum size.
        """
        file_size_bytes = file_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            raise FileValidationError(
                f"File size ({file_size_mb:.2f} MB) exceeds maximum "
                f"allowed size ({max_size_mb} MB)"
            )
        
        logger.info(f"File size: {file_size_mb:.2f} MB")
    
    def _load_csv(self, file_path: Path, 
                  **kwargs) -> pd.DataFrame:
        """
        Load data from CSV file with comprehensive error handling.
        
        Args:
            file_path: Path to CSV file.
            **kwargs: Additional pandas read_csv options.
            
        Returns:
            pd.DataFrame: Loaded data.
            
        Raises:
            DataLoadError: If CSV loading fails.
        """
        default_options = {
            'encoding': config.ENCODING,
            'low_memory': False,
            'na_values': list(config.MISSING_INDICATORS),
            'keep_default_na': True,
        }
        default_options.update(kwargs)
        
        try:
            logger.info(f"Loading CSV file: {file_path.name}")
            df = pd.read_csv(file_path, **default_options)
            logger.info(f"Successfully loaded {len(df)} rows from CSV")
            return df
            
        except pd.errors.EmptyDataError:
            raise DataLoadError(f"CSV file is empty: {file_path.name}")
        except pd.errors.ParserError as e:
            raise DataLoadError(f"CSV parsing error: {str(e)}")
        except UnicodeDecodeError:
            logger.warning("UTF-8 decoding failed, trying latin-1")
            try:
                default_options['encoding'] = 'latin-1'
                df = pd.read_csv(file_path, **default_options)
                return df
            except Exception as e:
                raise DataLoadError(f"Failed to decode CSV: {str(e)}")
        except Exception as e:
            raise DataLoadError(f"Unexpected error loading CSV: {str(e)}")
    
    def _load_excel(self, file_path: Path, 
                    sheet_name: Union[str, int] = 0,
                    **kwargs) -> pd.DataFrame:
        """
        Load data from Excel file with comprehensive error handling.
        
        Args:
            file_path: Path to Excel file.
            sheet_name: Sheet name or index to load.
            **kwargs: Additional pandas read_excel options.
            
        Returns:
            pd.DataFrame: Loaded data.
            
        Raises:
            DataLoadError: If Excel loading fails.
        """
        default_options = {
            'na_values': list(config.MISSING_INDICATORS),
            'keep_default_na': True,
        }
        default_options.update(kwargs)
        
        try:
            logger.info(f"Loading Excel file: {file_path.name}, sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name, **default_options)
            logger.info(f"Successfully loaded {len(df)} rows from Excel")
            return df
            
        except ValueError as e:
            if "Worksheet" in str(e):
                raise DataLoadError(f"Sheet not found: {sheet_name}")
            raise DataLoadError(f"Excel value error: {str(e)}")
        except ImportError:
            raise DataLoadError(
                "Excel loading requires 'openpyxl' or 'xlrd'. "
                "Install with: pip install openpyxl xlrd"
            )
        except Exception as e:
            raise DataLoadError(f"Unexpected error loading Excel: {str(e)}")
    
    def load(self, file_path: Optional[Union[str, Path]] = None,
             **kwargs) -> pd.DataFrame:
        """
        Main loading method with automatic file type detection.
        
        This is the primary entry point for loading data. It performs:
        1. File validation (exists, readable, size)
        2. Automatic file type detection
        3. Appropriate loading based on file type
        4. Metadata capture
        
        Args:
            file_path: Path to data file. Uses instance file_path if not provided.
            **kwargs: Additional loading options passed to pandas.
            
        Returns:
            pd.DataFrame: Loaded raw data.
            
        Raises:
            DataLoadError: If loading fails at any stage.
            FileValidationError: If file validation fails.
        """
        # Determine file path
        target_path = Path(file_path) if file_path else self.file_path
        
        if not target_path:
            raise DataLoadError("No file path provided. Set file_path in constructor or pass to load().")
        
        self.file_path = target_path
        
        # Step 1: Validate file
        self._validate_file_exists(target_path)
        self._validate_file_size(target_path)
        
        # Step 2: Detect file type
        self.file_type = self._detect_file_type(target_path)
        
        # Step 3: Load based on file type
        try:
            if self.file_type == 'csv':
                self.raw_data = self._load_csv(target_path, **kwargs)
            elif self.file_type == 'excel':
                self.raw_data = self._load_excel(target_path, **kwargs)
            else:
                raise DataLoadError(f"Unsupported file type for loading: {self.file_type}")
            
            # Capture metadata
            self.load_metadata = {
                'file_path': str(target_path.absolute()),
                'file_name': target_path.name,
                'file_type': self.file_type,
                'file_size_mb': round(target_path.stat().st_size / (1024 * 1024), 4),
                'rows_loaded': len(self.raw_data),
                'columns_loaded': len(self.raw_data.columns),
                'column_names': list(self.raw_data.columns),
                'timestamp': pd.Timestamp.now().isoformat(),
            }
            
            logger.info(
                f"Data loading completed successfully. "
                f"Shape: {self.raw_data.shape}, "
                f"Memory: {self.raw_data.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
            )
            
            return self.raw_data
            
        except Exception as e:
            logger.error(f"Data loading failed: {str(e)}")
            raise
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the last load operation.
        
        Returns:
            Dict[str, Any]: Load metadata dictionary.
        """
        return self.load_metadata.copy()
    
    def get_raw_data(self) -> Optional[pd.DataFrame]:
        """
        Get the loaded raw data.
        
        Returns:
            Optional[pd.DataFrame]: Raw data if loaded, None otherwise.
        """
        return self.raw_data.copy() if self.raw_data is not None else None


def load_data(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Convenience function for quick data loading.
    
    Args:
        file_path: Path to data file.
        **kwargs: Additional loading options.
        
    Returns:
        pd.DataFrame: Loaded data.
        
    Example:
        >>> df = load_data('data/raw/ecommerce_raw.csv')
        >>> df = load_data('data/raw/ecommerce_raw.xlsx', sheet_name='Orders')
    """
    loader = DataLoader(file_path)
    return loader.load(**kwargs)