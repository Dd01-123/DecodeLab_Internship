import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cleaning.config import config
from app.cleaning.pipeline import PipelineExecutionError
from app.core.orchestrator import AnalyticsPipeline
from app.eda.eda_pipeline import EDAPipelineError


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure file and console logging for the unified pipeline."""
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if verbose else getattr(logging, config.LOG_LEVEL))
    logger.handlers = []

    file_handler = logging.FileHandler(
        config.LOG_FILE,
        mode="w",
        encoding=config.ENCODING,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Unified E-Commerce Analytics Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m app.main\n"
            "  python app/main.py --input data/raw/ecommerce_raw.xlsx\n"
            "  python app/main.py -i raw.csv -o data/processed/ecommerce_cleaned.csv"
        ),
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default=str(config.RAW_DATA_FILE),
        help="Path to raw data file (CSV or Excel)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=str(config.CLEANED_DATA_FILE),
        help="Path for cleaned output file (CSV or Excel)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    logger = setup_logging(verbose=args.verbose)

    logger.info("=" * 80)
    logger.info("UNIFIED E-COMMERCE ANALYTICS PIPELINE")
    logger.info("=" * 80)
    logger.info("Version: 2.0.0")
    logger.info("Started: %s", datetime.now().isoformat())
    logger.info("Input File: %s", args.input)
    logger.info("Clean Output File: %s", args.output)
    logger.info("=" * 80)

    try:
        pipeline = AnalyticsPipeline(
            raw_file_path=Path(args.input),
            cleaned_file_path=Path(args.output),
        )
        context = pipeline.run()

        print("\n" + "=" * 80)
        print("UNIFIED PIPELINE EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Status:              SUCCESS")
        print(f"Raw Rows:            {context.cleaning_results.get('raw_rows', 0):,}")
        print(f"Cleaned Rows:        {context.cleaning_results.get('cleaned_rows', 0):,}")
        print(f"Rows Analyzed:       {context.eda_results.get('rows_analyzed', 0):,}")
        print(f"Duration:            {context.duration_seconds:.2f} seconds")
        print(f"Clean Dataset:       {context.cleaned_data_file}")
        print(f"Reports Generated:   {len(context.generated_reports)}")
        print(f"Visualizations:      {len(context.generated_visualizations)}")
        print(f"Final Report:        {context.reports_dir / 'final_pipeline_report.txt'}")
        print("=" * 80)

        return 0

    except (PipelineExecutionError, EDAPipelineError) as exc:
        logger.critical("Pipeline execution failed: %s", exc)
        print("\nERROR: Pipeline execution failed")
        print(f"   {exc}")
        print(f"\n   Check logs for details: {config.LOG_FILE}")
        return 1
    except Exception as exc:
        logger.critical("Unexpected error: %s", exc, exc_info=True)
        print("\nERROR: Unexpected error occurred")
        print(f"   {exc}")
        print(f"\n   Check logs for details: {config.LOG_FILE}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
