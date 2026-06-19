from pathlib import Path
from typing import Dict, List, Set

class PipelineConfig:
    """Centralized configuration for the data cleaning pipeline."""
    # ============================================================
    # DIRECTORY PATHS
    # ============================================================
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_RAW_DIR: Path = BASE_DIR / "data" / "raw"
    DATA_PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    LOGS_DIR: Path = BASE_DIR / "logs"
    REPORTS_DIR: Path = BASE_DIR / "reports"

    # ============================================================
    # FILE PATHS
    # ============================================================
    RAW_DATA_FILE: Path = DATA_RAW_DIR / "ecommerce_raw.xlsx"
    CLEANED_DATA_FILE: Path = DATA_PROCESSED_DIR / "ecommerce_cleaned.csv"
    ANALYTICS_DB_FILE: Path = DATA_PROCESSED_DIR / "analytics.db"
    SQL_DIR: Path = BASE_DIR / "sql"
    SQL_INSIGHTS_DIR: Path = REPORTS_DIR / "sql_insights"
    VISUALIZATION_REPORTS_DIR: Path = REPORTS_DIR / "visualization"
    LOG_FILE: Path = LOGS_DIR / "data_cleaning.log"
    QUALITY_REPORT_FILE: Path = REPORTS_DIR / "data_quality_report.txt"
    CLEANING_SUMMARY_FILE: Path = REPORTS_DIR / "cleaning_summary.txt"

    # ============================================================
    # COLUMN DEFINITIONS
    # ============================================================
    ALL_COLUMNS: List[str] = [
        "OrderID", "Date", "CustomerID", "Product", "Quantity",
        "UnitPrice", "ShippingAddress", "PaymentMethod", "OrderStatus",
        "TrackingNumber", "ItemsInCart", "CouponCode", "ReferralSource",
        "TotalPrice"
    ]
    
    NUMERIC_COLUMNS: List[str] = ["Quantity", "UnitPrice", "ItemsInCart", "TotalPrice"]
    CATEGORICAL_COLUMNS: List[str] = ["Product", "PaymentMethod", "OrderStatus", "ReferralSource"]
    DATE_COLUMNS: List[str] = ["Date"]
    TEXT_COLUMNS: List[str] = ["Product", "PaymentMethod", "OrderStatus", "ReferralSource", "CouponCode"]
    
    # ============================================================
    # MISSING VALUE INDICATORS
    # ============================================================
    MISSING_INDICATORS: Set[str] = {
        "", " ", "  ", "   ", "\\t", "\\n", "\\r",
        "nan", "NaN", "NAN", "<NA>", "None", "none", "NONE",
        "null", "Null", "NULL", "n/a", "N/A", "N/a", "n/A",
        "na", "NA", "Na", "nA", "unknown", "Unknown", "UNKNOWN",
        "missing", "Missing", "MISSING", "not available", "NOT AVAILABLE",
        "not applicable", "NOT APPLICABLE", "nil", "NIL", "Nil",
        "undefined", "UNDEFINED", "Undefined", "-", "--", "---"
    }
    
    # ============================================================
    # BUSINESS VALIDATION RULES
    # ============================================================
    VALID_ORDER_STATUSES: Set[str] = {
        "Pending", "Processing", "Shipped", "Delivered", 
        "Cancelled", "Returned"
    }
    
    ORDER_STATUS_MAPPING: Dict[str, str] = {
        # Pending variations
        "pending": "Pending",
        "PENDING": "Pending",
        "pendng": "Pending",
        "PENDNG": "Pending",
        # Processing variations
        "processing": "Processing",
        "PROCESSING": "Processing",
        "procesing": "Processing",
        "PROCESING": "Processing",
        # Shipped variations
        "shipped": "Shipped",
        "SHIPPED": "Shipped",
        "shiped": "Shipped",
        "SHIPED": "Shipped",
        # Delivered variations
        "delivered": "Delivered",
        "DELIVERED": "Delivered",
        "deliverd": "Delivered",
        "DELIVERD": "Delivered",
        "deliverred": "Delivered",
        "DELIVERRED": "Delivered",
        # Cancelled variations
        "cancelled": "Cancelled",
        "CANCELLED": "Cancelled",
        "canceled": "Cancelled",
        "CANCELED": "Cancelled",
        "canceld": "Cancelled",
        "CANCELD": "Cancelled",
        # Returned variations
        "returned": "Returned",
        "RETURNED": "Returned",
        "retuned": "Returned",
        "RETUNED": "Returned",
        "return": "Returned",
        "RETURN": "Returned",
    }
    
    PAYMENT_METHOD_MAPPING: Dict[str, str] = {
        # Credit Card variations
        "credit card": "Credit Card",
        "CREDIT CARD": "Credit Card",
        "CreditCard": "Credit Card",
        "creditcard": "Credit Card",
        "CREDITCARD": "Credit Card",
        "credit_card": "Credit Card",
        "Credit-Card": "Credit Card",
        "cc": "Credit Card",
        "CC": "Credit Card",
        # Debit Card variations
        "debit card": "Debit Card",
        "DEBIT CARD": "Debit Card",
        "DebitCard": "Debit Card",
        "debitcard": "Debit Card",
        "DEBITCARD": "Debit Card",
        "debit_card": "Debit Card",
        "Debit-Card": "Debit Card",
        "dc": "Debit Card",
        "DC": "Debit Card",
        # PayPal variations
        "paypal": "PayPal",
        "PAYPAL": "PayPal",
        "Paypal": "PayPal",
        # Cash on Delivery variations
        "cash on delivery": "Cash on Delivery",
        "CASH ON DELIVERY": "Cash on Delivery",
        "CashOnDelivery": "Cash on Delivery",
        "cashondelivery": "Cash on Delivery",
        "CASHONDELIVERY": "Cash on Delivery",
        "cod": "Cash on Delivery",
        "COD": "Cash on Delivery",
        "Cash On Delivery": "Cash on Delivery",
    }
    
    # ============================================================
    # DATA TYPE SETTINGS
    # ============================================================
    DATE_FORMAT: str = "%Y-%m-%d"
    ENCODING: str = "utf-8"
    
    # ============================================================
    # LOGGING SETTINGS
    # ============================================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(module)-15s | %(message)s"
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    
    # ============================================================
    # REPORTING SETTINGS
    # ============================================================
    REPORT_WIDTH: int = 80
    SEPARATOR: str = "=" * 80
    
    # ============================================================
    # VALIDATION THRESHOLDS
    # ============================================================
    MAX_MISSING_PERCENTAGE: float = 50.0  # Flag columns with >50% missing
    MIN_ROWS_FOR_PROCESSING: int = 1      # Minimum rows required

# Create a singleton instance for global access
config = PipelineConfig()
