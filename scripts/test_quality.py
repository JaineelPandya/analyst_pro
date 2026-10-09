from pathlib import Path
import json

from ingestion.xbrl.parser import XBRLParser
from ingestion.normalizer.periods import PeriodClassifier
from ingestion.normalizer.result import CompanyResultBuilder

from financial.features.features import (
    FinancialFeatureCalculator,
)

from financial.quality.earnings_quality import (
    EarningsQualityAnalyzer,
)


# ============================================================
# XBRL
# ============================================================

XBRL_FILE = Path(
    "data/raw/xbrl/INDAS_121092_1405515_29032025025828.xml"
)


# ============================================================
# Parse XBRL
# ============================================================

parser = XBRLParser(XBRL_FILE)

parser.parse()


# ============================================================
# Classify periods
# ============================================================

classifier = PeriodClassifier()


# ============================================================
# Build canonical result
# ============================================================

builder = CompanyResultBuilder(
    parser=parser,
    classifier=classifier,
)

result = builder.build()


# ============================================================
# Calculate financial features
# ============================================================

calculator = FinancialFeatureCalculator()

features = calculator.calculate(
    company_result=result,
    period="quarterly",
)


# ============================================================
# Analyze earnings quality
# ============================================================

analyzer = EarningsQualityAnalyzer()

quality = analyzer.analyze(
    features
)


# ============================================================
# Print
# ============================================================

print()
print("=" * 100)
print("EARNINGS QUALITY ANALYSIS")
print("=" * 100)

print()

print(
    json.dumps(
        analyzer.to_dict(quality),
        indent=2,
        ensure_ascii=False,
    )
)