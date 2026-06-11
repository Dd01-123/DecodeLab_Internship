## Overview

This project implements a complete **Phase 1: Data Cleaning & Data Preparation** pipeline for e-commerce data analytics. It follows industry standards used by Data Analysts, Data Scientists, and Data Engineers, featuring modular architecture, comprehensive logging, automated reporting, and strict data integrity rules.

**Key Principle:** The original dataset is **never modified**. The pipeline reads the raw dataset and creates a completely new cleaned dataset as output.

---

## Project Architecture

```
ecommerce_data_cleaning/
│
├── data/
│   ├── raw/
│   │   └── ecommerce_raw.csv          # Original dataset (READ-ONLY)
│   └── processed/
│       └── ecommerce_cleaned.csv      # Cleaned output dataset
│
├── logs/
│   └── data_cleaning.log              # Detailed execution logs
│
├── reports/
│   ├── data_quality_report.txt        # Initial data profiling report
│   └── cleaning_summary.txt           # Before/after comparison report
│
├── src/
│   ├── __init__.py                    # Package initialization
│   ├── config.py                      # Centralized configuration
│   ├── data_loader.py                 # Data loading with auto-detection
│   ├── cleaner.py                     # Data cleaning operations
│   ├── validator.py                   # Business rule validation
│   ├── reporter.py                    # Quality reporting
│   └── pipeline.py                    # Main orchestrator
│
├── requirements.txt                    # Python dependencies
├── main.py                             # Entry point script
└── README.md                           # This file
```

---

## Features

### 1. Data Loading Module
- Automatic file type detection (CSV, Excel)
- File validation (exists, readable, size limits)
- Comprehensive exception handling
- UTF-8 and fallback encoding support

### 2. Initial Data Assessment
- Complete dataset profiling
- Missing value analysis with percentage breakdown
- Duplicate detection
- Memory usage analysis
- Statistical summaries (mean, median, std, quartiles)

### 3. Missing Value Handling
- Detects all forms: NaN, Null, blank strings, whitespace, "Unknown", "N/A", "NA", "NULL"
- **Numeric columns:** Fill with median
- **Categorical columns:** Fill with mode
- **TrackingNumber:** Preserved as missing (business rule - may be genuinely unavailable)

### 4. Duplicate Handling
- Exact duplicate row detection and removal
- Detailed reporting of duplicates found and removed

### 5. Data Type Correction
- **Date:** Converts to datetime, handles invalid dates gracefully
- **Numeric:** Removes currency symbols (₹, $, €, £), commas, spaces, text contamination
- **Text:** Strips spaces, removes extra whitespace, normalizes capitalization

### 6. Business Validation Rules
| Rule | Description | Action |
|------|-------------|--------|
| Rule 1 | Quantity > 0 | Replace invalid with median |
| Rule 2 | UnitPrice > 0 | Replace invalid with median |
| Rule 3 | ItemsInCart >= Quantity | Set ItemsInCart = Quantity |
| Rule 4 | TotalPrice = Quantity × UnitPrice | Recalculate and correct |
| Rule 5 | OrderStatus standardization | Map to allowed values |
| Rule 6 | PaymentMethod standardization | Map to standard forms |

### 7. Logging System
- Enterprise-grade Python logging
- File and console handlers
- Detailed operation logs, errors, and exceptions
- Timestamped audit trail

### 8. Data Quality Reporting
- **Before Cleaning:** Total rows, columns, missing values, duplicates, invalid records
- **After Cleaning:** Same metrics post-processing
- **Improvement Summary:** Quantified fixes and corrections
- Quality score calculation

---

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Clone or Download the Project

```bash
cd ecommerce_data_cleaning
```

### Step 2: Create Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Basic Execution

```bash
python main.py
```

This uses the default paths:
- Input: `data/raw/ecommerce_raw.csv`
- Output: `data/processed/ecommerce_cleaned.csv`

### Custom Paths

```bash
# Custom input file
python main.py --input path/to/your/data.csv

# Custom output file
python main.py --output path/to/output/cleaned.csv

# Both custom paths
python main.py -i data/raw/my_data.xlsx -o data/processed/my_cleaned.csv

# Verbose logging
python main.py -v
```

### Programmatic Usage

```python
from src.pipeline import DataCleaningPipeline

# Initialize pipeline
pipeline = DataCleaningPipeline(
    raw_file_path="data/raw/ecommerce_raw.csv",
    output_file_path="data/processed/ecommerce_cleaned.csv"
)

# Run the pipeline
results = pipeline.run()

# Access results
print(f"Rows processed: {results['raw_rows']}")
print(f"Rows cleaned: {results['cleaned_rows']}")
print(f"Duration: {results['duration_seconds']:.2f}s")

# Print execution summary
print(pipeline.get_execution_summary())
```

---

## Configuration

All configuration is centralized in `src/config.py`. Key settings include:

| Setting | Description | Default |
|---------|-------------|---------|
| `RAW_DATA_FILE` | Input file path | `data/raw/ecommerce_raw.csv` |
| `CLEANED_DATA_FILE` | Output file path | `data/processed/ecommerce_cleaned.csv` |
| `MISSING_INDICATORS` | Values treated as missing | `{"", "NaN", "N/A", "NULL", ...}` |
| `VALID_ORDER_STATUSES` | Allowed order statuses | `{"Pending", "Processing", ...}` |
| `ENCODING` | File encoding | `utf-8` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## Output Files

### Cleaned Dataset
- **Location:** `data/processed/ecommerce_cleaned.csv`
- **Format:** CSV with UTF-8 encoding
- **Features:** No index column, original column order preserved

### Data Quality Report
- **Location:** `reports/data_quality_report.txt`
- **Contents:** Dataset overview, missing values, duplicates, statistics

### Cleaning Summary Report
- **Location:** `reports/cleaning_summary.txt`
- **Contents:** Before/after comparison, improvement metrics, quality scores

### Execution Log
- **Location:** `logs/data_cleaning.log`
- **Contents:** Timestamped operations, errors, corrections, exceptions

---

## Coding Standards

This project follows:
- **PEP 8** - Python style guide
- **Type Hints** - Full type annotation coverage
- **Docstrings** - Google-style documentation
- **Modular Design** - Single Responsibility Principle
- **SOLID Principles** - Object-oriented best practices
- **Reusable Functions** - DRY (Don't Repeat Yourself)
- **Proper Exception Handling** - Custom exceptions with context
- **Logging Best Practices** - Structured, informative logs
- **Configuration-Driven Design** - Centralized, maintainable settings

---

## Testing

### Sample Data
The project includes a sample `ecommerce_raw.csv` with intentional data quality issues for demonstration:
- Missing values (NaN, blank, "N/A", "NULL")
- Currency symbols and formatting issues
- Duplicate records
- Invalid dates
- Inconsistent capitalization
- Business rule violations

### Expected Results
After running the pipeline on the sample data, you should see:
- Cleaned dataset with standardized values
- Comprehensive reports in `reports/`
- Detailed execution log in `logs/`

---

## Project Roadmap

### Phase 1: Data Cleaning (Current)
- Data loading and validation
- Missing value handling
- Duplicate removal
- Data type correction
- Business rule validation
- Reporting and logging

### Phase 2: Data Transformation (Future)
- Feature engineering
- Data normalization
- Encoding categorical variables
- Outlier detection and handling

### Phase 3: Data Analysis (Future)
- Exploratory data analysis
- Statistical analysis
- Visualization generation
- Insight extraction

---

## License

This project is intended for educational and portfolio purposes.

---

## Author

**Data Engineering Team**
- Senior Data Analyst, Data Scientist, Data Engineering Architect
- Python Architect, Enterprise Software Engineer

---

## Contact & Support

For questions, issues, or contributions, please refer to the project documentation or contact the development team.

**Happy Data Cleaning!**