from pathlib import Path

from ingestion.xbrl.parser import XBRLParser
from ingestion.normalizer.periods import PeriodClassifier


XBRL_FILE = Path("data/raw/xbrl/INDAS_121092_1405515_29032025025828.xml")


parser = XBRLParser(XBRL_FILE)
parser.parse()

classifier = PeriodClassifier()


print()
print("=" * 80)
print("PERIOD CLASSIFICATION")
print("=" * 80)

for context_id, context in parser.contexts.items():

    result = classifier.classify(context)

    print()
    print(f"Context:       {result.context_id}")
    print(f"Type:          {result.period_type}")
    print(f"Start:         {result.start_date}")
    print(f"End:           {result.end_date}")
    print(f"Instant:       {result.instant}")
    print(f"Duration days: {result.duration_days}")
    print(f"Duration mos:  {result.duration_months}")
    print(f"Fiscal year:   {result.fiscal_year}")
    print(f"Quarter:       {result.quarter}")
    print(f"Confidence:    {result.confidence}")

    if result.warnings:
        print(f"Warnings:      {result.warnings}")