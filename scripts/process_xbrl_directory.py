from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ingestion.xbrl.parser import XBRLParser
from ingestion.normalizer.periods import PeriodClassifier
from ingestion.normalizer.result import CompanyResultBuilder

from financial.features.features import FinancialFeatureCalculator
from financial.quality.earnings_quality import EarningsQualityAnalyzer


# ============================================================
# HELPERS
# ============================================================

def dataclass_to_dict(value: Any) -> Any:
    """
    Convert dataclasses / nested structures into JSON-safe
    Python objects.
    """

    if value is None:
        return None

    if hasattr(value, "__dataclass_fields__"):
        result = {}

        for field_name in value.__dataclass_fields__:
            field_value = getattr(
                value,
                field_name,
            )

            result[field_name] = dataclass_to_dict(
                field_value
            )

        return result

    if isinstance(value, dict):
        return {
            key: dataclass_to_dict(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            dataclass_to_dict(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            dataclass_to_dict(item)
            for item in value
        ]

    return value


def get_xml_files(
    directory: Path,
) -> list[Path]:

    return sorted(
        directory.glob("*.xml")
    )


def extract_company_result_periods(
    result,
) -> list:

    periods = []

    for attribute in (
        "quarterly",
        "ytd",
        "annual",
        "instant",
    ):

        period = getattr(
            result,
            attribute,
            None,
        )

        if period is not None:
            periods.append(period)

    return periods


# ============================================================
# MAIN PROCESSOR
# ============================================================

class XBRLDirectoryProcessor:

    def __init__(
        self,
        input_directory: Path,
        output_directory: Path,
    ):

        self.input_directory = (
            input_directory
        )

        self.output_directory = (
            output_directory
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # Existing project components
        # ----------------------------------------------------

        self.classifier = PeriodClassifier()

        self.feature_calculator = (
            FinancialFeatureCalculator()
        )

        self.quality_analyzer = (
            EarningsQualityAnalyzer()
        )

    # ========================================================
    # PROCESS ONE FILE
    # ========================================================

    def process_file(
        self,
        xml_path: Path,
    ) -> dict:

        print()
        print("-" * 90)
        print(
            f"Processing: {xml_path.name}"
        )
        print("-" * 90)

        # ----------------------------------------------------
        # Parse
        # ----------------------------------------------------

        parser = XBRLParser(
            str(xml_path)
        )

        parsed = parser.parse()

        # ----------------------------------------------------
        # Build canonical result
        #
        # Your current CompanyResultBuilder expects:
        #
        # CompanyResultBuilder(parser, classifier)
        #
        # and build() takes no argument.
        # ----------------------------------------------------

        builder = CompanyResultBuilder(
            parser=parser,
            classifier=self.classifier,
        )

        result = builder.build()

        # ----------------------------------------------------
        # Extract periods
        # ----------------------------------------------------

        periods = (
            extract_company_result_periods(
                result
            )
        )

        processed_periods = []

        for period in periods:

            # ------------------------------------------------
            # Financial features
            # ------------------------------------------------

            try:

                features = (
                    self.feature_calculator.calculate(
                        period
                    )
                )

            except Exception as exc:

                print(
                    "[WARNING] Feature calculation "
                    f"failed: {exc}"
                )

                features = None

            # ------------------------------------------------
            # Earnings quality
            # ------------------------------------------------

            quality = None

            if features is not None:

                try:

                    quality = (
                        self.quality_analyzer.analyze(
                            features
                        )
                    )

                except Exception as exc:

                    print(
                        "[WARNING] Earnings quality "
                        f"analysis failed: {exc}"
                    )

            # ------------------------------------------------
            # Build period record
            # ------------------------------------------------

            period_record = {
                "period": dataclass_to_dict(
                    period
                ),
                "features": (
                    dataclass_to_dict(
                        features
                    )
                    if features is not None
                    else None
                ),
                "earnings_quality": (
                    dataclass_to_dict(
                        quality
                    )
                    if quality is not None
                    else None
                ),
            }

            processed_periods.append(
                period_record
            )

        # ====================================================
        # FINAL FILE RECORD
        # ====================================================

        output = {
            "source": {
                "file": str(xml_path),
                "filename": xml_path.name,
            },
            "company_result": (
                dataclass_to_dict(result)
            ),
            "periods": processed_periods,
        }

        return output

    # ========================================================
    # PROCESS DIRECTORY
    # ========================================================

    def process(self) -> dict:

        xml_files = get_xml_files(
            self.input_directory
        )

        print()
        print("=" * 100)
        print("XBRL DIRECTORY PROCESSING")
        print("=" * 100)

        print(
            f"Input directory : "
            f"{self.input_directory}"
        )

        print(
            f"XML files       : "
            f"{len(xml_files)}"
        )

        print("=" * 100)

        successful = []

        failed = []

        # ----------------------------------------------------
        # Process every XML
        # ----------------------------------------------------

        for index, xml_path in enumerate(
            xml_files,
            start=1,
        ):

            print()
            print(
                f"[{index}/{len(xml_files)}]"
            )

            try:

                result = self.process_file(
                    xml_path
                )

                successful.append(
                    result
                )

                print(
                    "STATUS: SUCCESS"
                )

            except Exception as exc:

                print(
                    "STATUS: FAILED"
                )

                print(
                    f"ERROR: {exc}"
                )

                failed.append(
                    {
                        "file": str(xml_path),
                        "error": str(exc),
                    }
                )

        # ====================================================
        # FINAL DATASET
        # ====================================================

        dataset = {
            "dataset": {
                "input_directory": str(
                    self.input_directory
                ),
                "total_files": len(xml_files),
                "successful_files": len(
                    successful
                ),
                "failed_files": len(
                    failed
                ),
            },
            "results": successful,
            "failures": failed,
        }

        return dataset

    # ========================================================
    # SAVE DATASET
    # ========================================================

    def save(
        self,
        dataset: dict,
        symbol: str,
    ) -> Path:

        output_path = (
            self.output_directory
            / f"{symbol.upper()}.json"
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                dataset,
                file,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        return output_path


# ============================================================
# CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Process a directory of NSE XBRL "
            "files through the financial "
            "intelligence pipeline."
        )
    )

    parser.add_argument(
        "--symbol",
        required=True,
        help="Company symbol, e.g. RELIANCE",
    )

    parser.add_argument(
        "--input-dir",
        default=None,
        help=(
            "Directory containing XBRL XML files. "
            "Defaults to data/raw/xbrl/<SYMBOL>"
        ),
    )

    parser.add_argument(
        "--output-dir",
        default="data/processed/financial_results",
        help=(
            "Directory for processed financial "
            "results."
        ),
    )

    args = parser.parse_args()

    # --------------------------------------------------------
    # Resolve directories
    # --------------------------------------------------------

    symbol = args.symbol.upper()

    if args.input_dir:

        input_directory = Path(
            args.input_dir
        )

    else:

        input_directory = (
            Path("data/raw/xbrl")
            / symbol
        )

    output_directory = Path(
        args.output_dir
    )

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not input_directory.exists():

        raise FileNotFoundError(
            "XBRL directory does not exist: "
            f"{input_directory}"
        )

    # --------------------------------------------------------
    # Process
    # --------------------------------------------------------

    processor = XBRLDirectoryProcessor(
        input_directory=input_directory,
        output_directory=output_directory,
    )

    dataset = processor.process()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_path = processor.save(
        dataset=dataset,
        symbol=symbol,
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 100)
    print("XBRL PROCESSING COMPLETE")
    print("=" * 100)

    print(
        f"Symbol              : {symbol}"
    )

    print(
        f"Files discovered     : "
        f"{dataset['dataset']['total_files']}"
    )

    print(
        f"Successfully parsed  : "
        f"{dataset['dataset']['successful_files']}"
    )

    print(
        f"Failed               : "
        f"{dataset['dataset']['failed_files']}"
    )

    print(
        f"Output               : "
        f"{output_path}"
    )

    print("=" * 100)


if __name__ == "__main__":
    main()