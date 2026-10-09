from ingestion.xbrl.parser import XBRLParser


FILE = "data/raw/xbrl/INDAS_121092_1405515_29032025025828.xml"


parser = XBRLParser(FILE)

data = parser.parse()


print("\nCONTEXTS")
print("=" * 60)

for context_id, context in data["contexts"].items():

    print(
        context_id,
        "=>",
        context
    )


print("\nUNITS")
print("=" * 60)

for unit_id, unit in data["units"].items():

    print(
        unit_id,
        "=>",
        unit
    )


print("\nFACTS")
print("=" * 60)

for fact in data["facts"]:

    if fact.numeric_value is not None:

        print(
            fact.concept,
            "=",
            fact.numeric_value,
            "| context:",
            fact.context_ref,
            "| unit:",
            fact.unit_ref
        )