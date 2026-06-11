import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

from app.cleaning.config import config
from app.cleaning.pipeline import DataCleaningPipeline, PipelineExecutionError


def setup_logging() -> logging.Logger:
    """
    Configure enterprise-grade logging with file and console handlers.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Ensure logs directory exists
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Clear existing handlers
    logger.handlers = []
    
    # File handler with rotation capability
    file_handler = logging.FileHandler(
        config.LOG_FILE, 
        mode='w',
        encoding=config.ENCODING
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(levelname)-8s | %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description='E-Commerce Data Cleaning Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples:  python main.py | python main.py --input data.csv | python main.py --output cleaned.csv | python main.py -i in.csv -o out.csv'
    )
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        default=str(config.RAW_DATA_FILE),
        help='Path to raw data file (CSV or Excel)'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=str(config.CLEANED_DATA_FILE),
        help='Path for cleaned output file'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main execution function.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Log startup information
    logger.info("=" * 80)
    logger.info("E-COMMERCE DATA CLEANING PIPELINE")
    logger.info("=" * 80)
    logger.info("Version: 1.0.0")
    logger.info("Started: %s", datetime.now().isoformat())
    logger.info("Input File: %s", args.input)
    logger.info("Output File: %s", args.output)
    logger.info("=" * 80)
    
    try:
        # Initialize and run pipeline
        pipeline = DataCleaningPipeline(
            raw_file_path=Path(args.input),
            output_file_path=Path(args.output)
        )
        
        results = pipeline.run()
        
        # Print execution summary
        print("\n" + "=" * 80)
        print(pipeline.get_execution_summary())
        
        # Print key statistics
        print("\n" + "=" * 80)
        print("KEY STATISTICS")
        print("=" * 80)
        print("  Raw Rows:        {:,}".format(results['raw_rows']))
        print("  Cleaned Rows:    {:,}".format(results['cleaned_rows']))
        print("  Rows Removed:    {:,}".format(results['rows_removed']))
        print("  Duration:        {:.2f} seconds".format(results['duration_seconds']))
        print("  Output File:     {}".format(results['output_file']))
        print("=" * 80)
        
        logger.info("Pipeline completed successfully")
        return 0
        
    except PipelineExecutionError as e:
        logger.critical("Pipeline execution failed: %s", str(e))
        print("\nERROR: Pipeline execution failed")
        print("   {}".format(str(e)))
        print("\n   Check logs for details: {}".format(config.LOG_FILE))
        return 1
        
    except Exception as e:
        logger.critical("Unexpected error: %s", str(e), exc_info=True)
        print("\nERROR: Unexpected error occurred")
        print("   {}".format(str(e)))
        print("\n   Check logs for details: {}".format(config.LOG_FILE))
        return 1


if __name__ == '__main__':
    sys.exit(main())