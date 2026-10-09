import json

from ingestion.xbrl.parser import XBRLParser
from ingestion.normalizer.periods import PeriodClassifier
from ingestion.normalizer.result import (
    CompanyResultBuilder,
    FinancialPeriod,
)

from financial.comparisons.historical import (
    HistoricalComparisonEngine,
)


XML_PATH = (
    "data/raw/xbrl/"
    "INDAS_121092_1405515_29032025025828.xml"
)


def main():

    # ========================================================
    # 1. Parse XBRL
    # ========================================================

    parser = XBRLParser(XML_PATH)
    parsed = parser.parse()

    # ========================================================
    # 2. Create period classifier
    # ========================================================

    classifier = PeriodClassifier()

    # ========================================================
    # 3. Build canonical financial result
    # ========================================================

    builder = CompanyResultBuilder(
        parser=parser,
        classifier=classifier,
    )

    result = builder.build()

    # ========================================================
    # 4. Get current quarterly period
    # ========================================================

    current_period = result.quarterly

    if current_period is None:
        raise RuntimeError(
            "Quarterly financial period not found."
        )

    # ========================================================
    # 5. Synthetic previous quarter
    #
    # This is ONLY for testing the comparison engine.
    # Later this will come from real historical XBRL data.
    # ========================================================

    previous_period = FinancialPeriod(
        period_type="quarterly",
        start_date="2024-07-01",
        end_date="2024-09-30",
        fiscal_year="FY2025",
        quarter="Q2",
        metrics={
            "revenue": 60_000_000,
            "other_income": 20_000_000,
            "total_income": 80_000_000,
            "total_expenses": 40_000_000,
            "finance_cost": 2_000_000,
            "depreciation": 700_000,
            "pbt_before_exceptional": 38_000_000,
            "exceptional_items": 0,
            "pbt": 38_000_000,
            "pat": 38_000_000,
            "eps_basic": 2.50,
        },
    )

    # ========================================================
    # 6. Historical comparison
    # ========================================================

    engine = HistoricalComparisonEngine()

    comparison = engine.compare(
        current_period=current_period,
        previous_period=previous_period,
        comparison_type="QoQ",
    )

    # ========================================================
    # 7. Print result
    # ========================================================

    print()
    print("=" * 100)
    print("HISTORICAL COMPARISON")
    print("=" * 100)

    print(
        json.dumps(
            engine.to_dict(comparison),
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()