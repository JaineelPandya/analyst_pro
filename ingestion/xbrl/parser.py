from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional
import json
import re
import xml.etree.ElementTree as ET


XBRLI_NS = "http://www.xbrl.org/2003/instance"
XLINK_NS = "http://www.w3.org/1999/xlink"

NS = {
    "xbrli": XBRLI_NS,
    "xbrldi": "http://xbrl.org/2006/xbrldi",
    "link": "http://www.xbrl.org/2003/linkbase",
}


@dataclass
class Context:
    context_id: str

    # Entity
    identifier: Optional[str] = None
    identifier_scheme: Optional[str] = None

    # Period
    period_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    instant: Optional[str] = None

    # Scenario / dimensions
    dimensions: Optional[dict] = None


@dataclass
class Unit:
    unit_id: str
    measure: Optional[str] = None

    numerator: Optional[str] = None
    denominator: Optional[str] = None


@dataclass
class Fact:
    concept: str
    namespace: str

    context_ref: Optional[str] = None
    unit_ref: Optional[str] = None

    value: Optional[str] = None
    numeric_value: Optional[float] = None

    decimals: Optional[str] = None

    # Derived metadata
    context: Optional[dict] = None
    unit: Optional[dict] = None


class XBRLParser:

    def __init__(self, file_path: str | Path):

        self.file_path = Path(file_path)

        if not self.file_path.exists():
            raise FileNotFoundError(
                f"XBRL file not found: {self.file_path}"
            )

        self.tree = ET.parse(self.file_path)
        self.root = self.tree.getroot()

        self.namespaces = self._extract_namespaces()

        self.contexts: dict[str, Context] = {}
        self.units: dict[str, Unit] = {}
        self.facts: list[Fact] = []

    # ---------------------------------------------------------
    # Namespace extraction
    # ---------------------------------------------------------

    def _extract_namespaces(self):

        namespaces = {}

        for event, elem in ET.iterparse(
            self.file_path,
            events=("start-ns",)
        ):
            prefix, uri = elem

            namespaces[prefix or "default"] = uri

        return namespaces

    # ---------------------------------------------------------
    # Parse everything
    # ---------------------------------------------------------

    def parse(self):

        self.parse_contexts()
        self.parse_units()
        self.parse_facts()

        return {
            "contexts": self.contexts,
            "units": self.units,
            "facts": self.facts,
        }

    # ---------------------------------------------------------
    # Contexts
    # ---------------------------------------------------------

    def parse_contexts(self):

        for context_elem in self.root.findall(
            f"{{{XBRLI_NS}}}context"
        ):

            context_id = context_elem.get("id")

            context = Context(
                context_id=context_id,
                dimensions={}
            )

            # -----------------------------
            # Entity
            # -----------------------------

            entity = context_elem.find(
                f"{{{XBRLI_NS}}}entity"
            )

            if entity is not None:

                identifier = entity.find(
                    f"{{{XBRLI_NS}}}identifier"
                )

                if identifier is not None:

                    context.identifier = identifier.text
                    context.identifier_scheme = (
                        identifier.get("scheme")
                    )

            # -----------------------------
            # Period
            # -----------------------------

            period = context_elem.find(
                f"{{{XBRLI_NS}}}period"
            )

            if period is not None:

                start = period.find(
                    f"{{{XBRLI_NS}}}startDate"
                )

                end = period.find(
                    f"{{{XBRLI_NS}}}endDate"
                )

                instant = period.find(
                    f"{{{XBRLI_NS}}}instant"
                )

                if start is not None and end is not None:

                    context.period_type = "duration"

                    context.start_date = start.text
                    context.end_date = end.text

                elif instant is not None:

                    context.period_type = "instant"

                    context.instant = instant.text

            # -----------------------------
            # Scenario / Dimensions
            # -----------------------------

            scenario = context_elem.find(
                f"{{{XBRLI_NS}}}scenario"
            )

            if scenario is not None:

                for member in scenario:

                    tag = member.tag.split("}")[-1]

                    if tag == "explicitMember":

                        dimension = member.get("dimension")
                        value = member.text

                        context.dimensions[
                            dimension
                        ] = value

            self.contexts[context_id] = context

    # ---------------------------------------------------------
    # Units
    # ---------------------------------------------------------

    def parse_units(self):

        for unit_elem in self.root.findall(
            f"{{{XBRLI_NS}}}unit"
        ):

            unit_id = unit_elem.get("id")

            measure = unit_elem.find(
                f"{{{XBRLI_NS}}}measure"
            )

            unit = Unit(
                unit_id=unit_id
            )

            if measure is not None:

                unit.measure = measure.text

            else:

                divide = unit_elem.find(
                    f"{{{XBRLI_NS}}}divide"
                )

                if divide is not None:

                    numerator = divide.find(
                        f"{{{XBRLI_NS}}}unitNumerator/"
                        f"{{{XBRLI_NS}}}measure"
                    )

                    denominator = divide.find(
                        f"{{{XBRLI_NS}}}unitDenominator/"
                        f"{{{XBRLI_NS}}}measure"
                    )

                    if numerator is not None:
                        unit.numerator = numerator.text

                    if denominator is not None:
                        unit.denominator = denominator.text

            self.units[unit_id] = unit

    # ---------------------------------------------------------
    # Facts
    # ---------------------------------------------------------

    def parse_facts(self):

        # XBRL facts are direct children of xbrl instance
        for element in self.root:

            # Skip XBRL infrastructure
            if element.tag in {
                f"{{{XBRLI_NS}}}context",
                f"{{{XBRLI_NS}}}unit",
            }:
                continue

            # Remove namespace
            if "}" in element.tag:

                namespace, local_name = element.tag[1:].split(
                    "}",
                    1
                )

            else:

                namespace = ""
                local_name = element.tag

            context_ref = element.get("contextRef")
            unit_ref = element.get("unitRef")
            decimals = element.get("decimals")

            value = element.text.strip() if element.text else None

            numeric_value = self._parse_numeric(value)

            context_data = None

            if context_ref in self.contexts:

                context_data = asdict(
                    self.contexts[context_ref]
                )

            unit_data = None

            if unit_ref in self.units:

                unit_data = asdict(
                    self.units[unit_ref]
                )

            fact = Fact(
                concept=local_name,
                namespace=namespace,
                context_ref=context_ref,
                unit_ref=unit_ref,
                value=value,
                numeric_value=numeric_value,
                decimals=decimals,
                context=context_data,
                unit=unit_data,
            )

            self.facts.append(fact)

    # ---------------------------------------------------------
    # Numeric conversion
    # ---------------------------------------------------------

    @staticmethod
    def _parse_numeric(value: Optional[str]):

        if value is None:
            return None

        value = value.strip()

        try:

            return float(
                Decimal(value)
            )

        except Exception:

            return None

    # ---------------------------------------------------------
    # Get facts by concept
    # ---------------------------------------------------------

    def get_fact(self, concept: str):

        return [
            fact
            for fact in self.facts
            if fact.concept == concept
        ]

    # ---------------------------------------------------------
    # Export
    # ---------------------------------------------------------

    def to_json(self, output_path: str):

        data = {

            "contexts": {
                key: asdict(value)
                for key, value in self.contexts.items()
            },

            "units": {
                key: asdict(value)
                for key, value in self.units.items()
            },

            "facts": [
                asdict(fact)
                for fact in self.facts
            ],
        }

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False
            )