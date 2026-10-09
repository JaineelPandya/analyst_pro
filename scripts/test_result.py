from pathlib import Path
import json

from ingestion.xbrl.parser import XBRLParser
from ingestion.normalizer.periods import PeriodClassifier
from ingestion.normalizer.result import CompanyResultBuilder


XBRL_FILE = Path(
    "data/raw/xbrl/INDAS_121092_1405515_29032025025828.xml"
)


# ============================================================
# Parse XBRL
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
# Print
# ============================================================

print()
print("=" * 100)
print("CANONICAL FINANCIAL RESULT")
print("=" * 100)

print(
    json.dumps(
        builder.to_dict(result),
        indent=2,
        ensure_ascii=False,
    )
)