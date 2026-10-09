from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


# ============================================================
# Canonical Financial Result
# ============================================================


@dataclass
class FinancialPeriod:
    """
    Normalized financial data for one reporting period.

    period_type:
        quarterly
        ytd
        annual
        instant
    """

    period_type: str

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    instant: Optional[str] = None

    fiscal_year: Optional[str] = None
    quarter: Optional[str] = None

    metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class CompanyResult:
    """
    Canonical representation of one company's XBRL financial result.
    """

    company: Optional[str] = None
    financial_year: Optional[str] = None
    quarter: Optional[str] = None

    # Reporting metadata
    identifier_scheme: Optional[str] = None

    # Period-specific financial data
    quarterly: Optional[FinancialPeriod] = None
    ytd: Optional[FinancialPeriod] = None
    annual: Optional[FinancialPeriod] = None
    instant: Optional[FinancialPeriod] = None

    # Validation information
    warnings: list[str] = field(default_factory=list)


# ============================================================
# XBRL Concept → Canonical Metric
# ============================================================


CONCEPT_MAP = {

    # --------------------------------------------------------
    # Income
    # --------------------------------------------------------

    "RevenueFromOperations": "revenue",
    "OtherIncome": "other_income",
    "Income": "total_income",

    # --------------------------------------------------------
    # Expenses
    # --------------------------------------------------------

    "CostOfMaterialsConsumed": "cost_of_materials",

    "PurchasesOfStockInTrade": "purchases",

    "ChangesInInventoriesOfFinishedGoodsWorkInProgressAndStockInTrade":
        "inventory_change",

    "EmployeeBenefitExpense": "employee_expense",

    "FinanceCosts": "finance_cost",

    "DepreciationDepletionAndAmortisationExpense":
        "depreciation",

    "OtherExpenses": "other_expenses",

    "Expenses": "total_expenses",

    # --------------------------------------------------------
    # Profitability
    # --------------------------------------------------------

    "ProfitBeforeExceptionalItemsAndTax":
        "pbt_before_exceptional",

    "ExceptionalItemsBeforeTax":
        "exceptional_items",

    "ProfitBeforeTax":
        "pbt",

    "CurrentTax":
        "current_tax",

    "DeferredTax":
        "deferred_tax",

    "TaxExpense":
        "tax_expense",

    "ProfitLossForPeriod":
        "pat",

    "ProfitLossForPeriodFromContinuingOperations":
        "pat_continuing",

    "ComprehensiveIncomeForThePeriod":
        "comprehensive_income",

    # --------------------------------------------------------
    # Equity
    # --------------------------------------------------------

    "PaidUpValueOfEquityShareCapital":
        "paid_up_equity",

    "FaceValueOfEquityShareCapital":
        "face_value",

    # --------------------------------------------------------
    # EPS
    # --------------------------------------------------------

    "BasicEarningsLossPerShareFromContinuingOperations":
        "eps_basic",

    "DilutedEarningsLossPerShareFromContinuingOperations":
        "eps_diluted",

    "BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations":
        "eps_basic_total",

    "DilutedEarningsLossPerShareFromContinuingAndDiscontinuedOperations":
        "eps_diluted_total",

    # --------------------------------------------------------
    # Leverage / Coverage
    # --------------------------------------------------------

    "DebtEquityRatio":
        "debt_equity_ratio",

    "DebtServiceCoverageRatio":
        "debt_service_coverage_ratio",

    "InterestServiceCoverageRatio":
        "interest_service_coverage_ratio",
}


# ============================================================
# BSE Ind-AS Context Role Hints
# ============================================================

"""
Some BSE Ind-AS XBRL files use context IDs such as:

    OneD
    FourD

where the dates can sometimes be identical even though the
facts represent different reporting roles.

For this taxonomy:

    OneD  → quarterly
    FourD → YTD

We use this ONLY when the context ID matches the known pattern.

The actual context dates are still retained and validated.

This prevents FourD facts from overwriting OneD facts.
"""

CONTEXT_ROLE_HINTS = {
    "OneD": "quarterly",
    "FourD": "ytd",

    # Dimensional versions used in some BSE files
    "OneOperatingExpenses01D": "quarterly",
    "FourOperatingExpenses01D": "ytd",
}


# ============================================================
# Result Builder
# ============================================================


class CompanyResultBuilder:
    """
    Converts parsed XBRL facts into a canonical CompanyResult.

    Pipeline:

        XBRLParser
             ↓
        PeriodClassifier
             ↓
        CompanyResultBuilder
             ↓
        CompanyResult
    """

    def __init__(self, parser, classifier):

        self.parser = parser
        self.classifier = classifier

    # ========================================================
    # Public API
    # ========================================================

    def build(self) -> CompanyResult:

        result = CompanyResult()

        # ----------------------------------------------------
        # Classify contexts
        # ----------------------------------------------------

        classified_contexts = {}

        for context_id, context in self.parser.contexts.items():

            classification = self.classifier.classify(context)

            # Apply known BSE context role when available.
            classification = self._apply_context_role(
                context_id=context_id,
                classification=classification,
                result=result,
            )

            classified_contexts[context_id] = classification

        # ----------------------------------------------------
        # Process facts
        # ----------------------------------------------------

        for fact in self.parser.facts:

            context_id = fact.context_ref

            if context_id not in classified_contexts:
                continue

            classification = classified_contexts[context_id]

            # ------------------------------------------------
            # Skip unknown periods
            # ------------------------------------------------

            if classification.period_type == "other":

                result.warnings.append(
                    f"SKIPPED_UNKNOWN_PERIOD: "
                    f"fact='{fact.concept}', "
                    f"context='{context_id}'"
                )

                continue

            # ------------------------------------------------
            # Skip unmapped concepts
            # ------------------------------------------------

            metric = CONCEPT_MAP.get(fact.concept)

            if metric is None:
                continue

            # ------------------------------------------------
            # Skip non-numeric facts
            # ------------------------------------------------

            if fact.numeric_value is None:
                continue

            # ------------------------------------------------
            # Get target period
            # ------------------------------------------------

            period = self._get_or_create_period(
                result=result,
                classification=classification,
            )

            # ------------------------------------------------
            # Duplicate protection
            # ------------------------------------------------

            if metric in period.metrics:

                existing_value = period.metrics[metric]

                # Same metric + same value is harmless.
                if existing_value == fact.numeric_value:
                    continue

                result.warnings.append(
                    f"DUPLICATE_METRIC: "
                    f"metric='{metric}', "
                    f"period='{classification.period_type}', "
                    f"existing={existing_value}, "
                    f"new={fact.numeric_value}, "
                    f"context='{context_id}'"
                )

                # IMPORTANT:
                # Never silently overwrite financial data.
                continue

            # ------------------------------------------------
            # Store metric
            # ------------------------------------------------

            period.metrics[metric] = fact.numeric_value

        # ----------------------------------------------------
        # Derive metadata
        # ----------------------------------------------------

        self._derive_metadata(result)

        return result

    # ========================================================
    # Context Role
    # ========================================================

    def _apply_context_role(
        self,
        context_id,
        classification,
        result,
    ):

        hinted_type = CONTEXT_ROLE_HINTS.get(context_id)

        if hinted_type is None:
            return classification

        # ----------------------------------------------------
        # Validate the hint against the actual dates
        # ----------------------------------------------------

        if hinted_type == "quarterly":

            if classification.period_type != "quarterly":

                result.warnings.append(
                    f"CONTEXT_ROLE_OVERRIDE: "
                    f"context='{context_id}' "
                    f"classifier='{classification.period_type}' "
                    f"overridden='quarterly'"
                )

            classification.period_type = "quarterly"

        elif hinted_type == "ytd":

            if classification.period_type != "ytd":

                result.warnings.append(
                    f"CONTEXT_ROLE_OVERRIDE: "
                    f"context='{context_id}' "
                    f"classifier='{classification.period_type}' "
                    f"overridden='ytd'"
                    f"dates={classification.start_date}->{classification.end_date}"
                )

            classification.period_type = "ytd"

        return classification

    # ========================================================
    # Period Handling
    # ========================================================

    def _get_or_create_period(
        self,
        result: CompanyResult,
        classification,
    ) -> FinancialPeriod:

        period_type = classification.period_type

        # ----------------------------------------------------
        # Quarterly
        # ----------------------------------------------------

        if period_type == "quarterly":

            if result.quarterly is None:

                result.quarterly = FinancialPeriod(
                    period_type="quarterly",
                    start_date=classification.start_date,
                    end_date=classification.end_date,
                    fiscal_year=classification.fiscal_year,
                    quarter=classification.quarter,
                )

            return result.quarterly

        # ----------------------------------------------------
        # YTD
        # ----------------------------------------------------

        if period_type == "ytd":

            if result.ytd is None:

                result.ytd = FinancialPeriod(
                    period_type="ytd",
                    start_date=classification.start_date,
                    end_date=classification.end_date,
                    fiscal_year=classification.fiscal_year,
                    quarter=classification.quarter,
                )

            return result.ytd

        # ----------------------------------------------------
        # Annual
        # ----------------------------------------------------

        if period_type == "annual":

            if result.annual is None:

                result.annual = FinancialPeriod(
                    period_type="annual",
                    start_date=classification.start_date,
                    end_date=classification.end_date,
                    fiscal_year=classification.fiscal_year,
                )

            return result.annual

        # ----------------------------------------------------
        # Instant
        # ----------------------------------------------------

        if period_type == "instant":

            if result.instant is None:

                result.instant = FinancialPeriod(
                    period_type="instant",
                    instant=classification.instant,
                )

            return result.instant

        raise ValueError(
            f"Unsupported period type: {period_type}"
        )

    # ========================================================
    # Metadata
    # ========================================================

    def _derive_metadata(
        self,
        result: CompanyResult,
    ):

        # ----------------------------------------------------
        # Prefer quarterly
        # ----------------------------------------------------

        primary_period = (
            result.quarterly
            or result.ytd
            or result.annual
        )

        if primary_period:

            result.financial_year = (
                primary_period.fiscal_year
            )

            result.quarter = (
                primary_period.quarter
            )

        # ----------------------------------------------------
        # Company identifier
        # ----------------------------------------------------

        for context in self.parser.contexts.values():

            if context.identifier:

                result.company = context.identifier

                result.identifier_scheme = (
                    context.identifier_scheme
                )

                break

    # ========================================================
    # JSON
    # ========================================================

    def to_dict(
        self,
        result: CompanyResult,
    ) -> dict:

        return asdict(result)