from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Optional


# ============================================================
# SIGNAL
# ============================================================

@dataclass
class EarningsQualitySignal:
    code: str
    name: str
    severity: str
    description: str
    evidence: dict = field(default_factory=dict)


# ============================================================
# RESULT
# ============================================================

@dataclass
class EarningsQualityResult:
    signals: list[EarningsQualitySignal] = field(
        default_factory=list
    )

    quality_score: Optional[float] = None
    quality_label: Optional[str] = None


# ============================================================
# ANALYZER
# ============================================================

class EarningsQualityAnalyzer:

    def analyze(self, features) -> EarningsQualityResult:

        signals = []

        # 1. Exceptional items
        self._check_exceptional_items(
            features,
            signals
        )

        # 2. Other income
        self._check_other_income(
            features,
            signals
        )

        # 3. Finance cost
        self._check_finance_cost(
            features,
            signals
        )

        # 4. Underlying profitability
        self._check_underlying_profitability(
            features,
            signals
        )

        # 5. Expense structure
        self._check_expense_structure(
            features,
            signals
        )

        # Calculate score
        score = self._calculate_score(signals)

        # Calculate label
        label = self._score_label(score)

        return EarningsQualityResult(
            signals=signals,
            quality_score=score,
            quality_label=label
        )

    # ========================================================
    # EXCEPTIONAL ITEMS
    # ========================================================

    @staticmethod
    def _check_exceptional_items(features, signals):

        ratio = features.exceptional_item_to_pbt_before_exceptional
        revenue_ratio = features.exceptional_item_ratio

        if ratio is None:
            return

        if abs(ratio) >= 1.0:

            signal = EarningsQualitySignal(
                code="EXCEPTIONAL_ITEM_DRIVEN_EARNINGS",
                name="Exceptional-item driven earnings",
                severity="critical",
                description=(
                    "Reported earnings are materially "
                    "influenced by an exceptional item "
                    "relative to pre-exceptional profit."
                ),
                evidence={
                    "exceptional_item_to_pbt_before_exceptional": ratio,
                    "exceptional_item_ratio": revenue_ratio
                }
            )

            signals.append(signal)

        elif abs(ratio) >= 0.50:

            signal = EarningsQualitySignal(
                code="HIGH_EXCEPTIONAL_ITEM_DEPENDENCY",
                name="High exceptional-item dependency",
                severity="high",
                description=(
                    "Exceptional items represent a substantial "
                    "portion of underlying profitability."
                ),
                evidence={
                    "exceptional_item_to_pbt_before_exceptional": ratio,
                    "exceptional_item_ratio": revenue_ratio
                }
            )

            signals.append(signal)

    # ========================================================
    # OTHER INCOME
    # ========================================================

    @staticmethod
    def _check_other_income(features, signals):

        ratio = features.other_income_ratio

        if ratio is None:
            return

        if abs(ratio) >= 1.0:

            signal = EarningsQualitySignal(
                code="OTHER_INCOME_DOMINATES_REVENUE",
                name="Other income exceeds operating revenue",
                severity="critical",
                description=(
                    "Other income is larger than operating "
                    "revenue and materially affects reported "
                    "profitability."
                ),
                evidence={
                    "other_income_ratio": ratio
                }
            )

            signals.append(signal)

        elif abs(ratio) >= 0.50:

            signal = EarningsQualitySignal(
                code="OTHER_INCOME_DEPENDENCY",
                name="High other-income dependency",
                severity="high",
                description=(
                    "Other income represents a substantial "
                    "share of operating revenue."
                ),
                evidence={
                    "other_income_ratio": ratio
                }
            )

            signals.append(signal)

    # ========================================================
    # FINANCE COST
    # ========================================================

    @staticmethod
    def _check_finance_cost(features, signals):

        ratio = features.finance_cost_ratio

        if ratio is None:
            return

        if abs(ratio) >= 0.20:

            signal = EarningsQualitySignal(
                code="HIGH_FINANCE_COST_PRESSURE",
                name="High finance-cost pressure",
                severity="high",
                description=(
                    "Finance costs represent a significant "
                    "share of revenue."
                ),
                evidence={
                    "finance_cost_ratio": ratio
                }
            )

            signals.append(signal)

        elif abs(ratio) >= 0.10:

            signal = EarningsQualitySignal(
                code="MODERATE_FINANCE_COST_PRESSURE",
                name="Moderate finance-cost pressure",
                severity="medium",
                description=(
                    "Finance costs represent a meaningful "
                    "share of revenue."
                ),
                evidence={
                    "finance_cost_ratio": ratio
                }
            )

            signals.append(signal)

    # ========================================================
    # UNDERLYING PROFITABILITY
    # ========================================================

    @staticmethod
    def _check_underlying_profitability(features, signals):

        underlying = features.underlying_pbt
        reported_pat = features.pat

        if underlying is None:
            return

        if reported_pat is None:
            return

        # Underlying loss
        if underlying < 0:

            signal = EarningsQualitySignal(
                code="UNDERLYING_LOSS",
                name="Underlying business loss",
                severity="critical",
                description=(
                    "Pre-exceptional profit is negative, "
                    "indicating an underlying loss."
                ),
                evidence={
                    "underlying_pbt": underlying,
                    "reported_pat": reported_pat
                }
            )

            signals.append(signal)

        # Reported vs underlying divergence
        ratio = features.reported_pat_to_underlying_pbt

        if ratio is not None and ratio >= 5:

            signal = EarningsQualitySignal(
                code="REPORTED_UNDERLYING_PROFIT_DIVERGENCE",
                name="Reported vs underlying profit divergence",
                severity="high",
                description=(
                    "Reported profit is substantially larger "
                    "than the underlying pre-exceptional profit."
                ),
                evidence={
                    "reported_pat_to_underlying_pbt": ratio,
                    "underlying_pbt": underlying,
                    "reported_pat": reported_pat
                }
            )

            signals.append(signal)

    # ========================================================
    # EXPENSE STRUCTURE
    # ========================================================

    @staticmethod
    def _check_expense_structure(features, signals):

        ratio = features.expense_ratio

        if ratio is None:
            return

        if ratio >= 1.0:

            signal = EarningsQualitySignal(
                code="EXPENSES_EXCEED_REVENUE",
                name="Expenses exceed revenue",
                severity="critical",
                description=(
                    "Reported expenses exceed operating revenue."
                ),
                evidence={
                    "expense_ratio": ratio
                }
            )

            signals.append(signal)

        elif ratio >= 0.90:

            signal = EarningsQualitySignal(
                code="HIGH_EXPENSE_INTENSITY",
                name="High expense intensity",
                severity="medium",
                description=(
                    "Expenses consume most of operating revenue."
                ),
                evidence={
                    "expense_ratio": ratio
                }
            )

            signals.append(signal)

    # ========================================================
    # SCORE
    # ========================================================

    @staticmethod
    def _calculate_score(signals):

        score = 100.0

        penalties = {
            "low": 5,
            "medium": 10,
            "high": 20,
            "critical": 35
        }

        for signal in signals:

            penalty = penalties.get(
                signal.severity,
                0
            )

            score -= penalty

        score = max(
            0.0,
            min(100.0, score)
        )

        return score

    # ========================================================
    # LABEL
    # ========================================================

    @staticmethod
    def _score_label(score):

        if score >= 80:
            return "strong"

        if score >= 60:
            return "moderate"

        if score >= 40:
            return "weak"

        return "poor"

    # ========================================================
    # JSON
    # ========================================================

    @staticmethod
    def to_dict(result):

        return asdict(result)