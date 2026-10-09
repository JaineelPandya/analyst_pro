from pathlib import Path
import json

from ingestion.xbrl.parser import XBRLParser
from ingestion.normalizer.periods import PeriodClassifier
from ingestion.normalizer.result import CompanyResultBuilder

from financial.features.features import (
    FinancialFeatureCalculator,
)


# ============================================================
# XBRL
# ============================================================

XBRL_FILE = Path(
    "data/raw/xbrl/INDAS_121092_1405515_29032025025828.xml"
)


# ============================================================
# Parse
# ============================================================

parser = XBRLParser(XBRL_FILE)

parser.parse()


# ============================================================
# Period classification
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
# Calculate features
# ============================================================

calculator = FinancialFeatureCalculator()

features = calculator.calculate(
    company_result=result,
    period="quarterly",
)


# ============================================================
# Print
# ============================================================

print()
print("=" * 100)
print("FINANCIAL FEATURES")
print("=" * 100)

print(
    json.dumps(
        calculator.to_dict(features),
        indent=2,
        ensure_ascii=False,
    )
)