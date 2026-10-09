from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional


# ============================================================
# Feature Result
# ============================================================


@dataclass
class FinancialFeatures:
    """
    Derived numerical features from one financial result.

    All ratio features are represented as decimals.

    Example:
        0.25 = 25%
    """

    # --------------------------------------------------------
    # Basic values
    # --------------------------------------------------------

    revenue: Optional[float] = None
    other_income: Optional[float] = None
    total_income: Optional[float] = None

    total_expenses: Optional[float] = None
    finance_cost: Optional[float] = None
    depreciation: Optional[float] = None

    pbt_before_exceptional: Optional[float] = None
    exceptional_items: Optional[float] = None
    pbt: Optional[float] = None
    pat: Optional[float] = None

    eps_basic: Optional[float] = None

    # --------------------------------------------------------
    # Margin features
    # --------------------------------------------------------

    pbt_margin: Optional[float] = None
    pat_margin: Optional[float] = None

    # --------------------------------------------------------
    # Income quality
    # --------------------------------------------------------

    other_income_ratio: Optional[float] = None

    exceptional_item_ratio: Optional[float] = None

    exceptional_item_to_pbt_before_exceptional: Optional[float] = None

    reported_pbt_to_underlying_pbt: Optional[float] = None

    reported_pat_to_underlying_pbt: Optional[float] = None

    # --------------------------------------------------------
    # Expense structure
    # --------------------------------------------------------

    expense_ratio: Optional[float] = None

    finance_cost_ratio: Optional[float] = None

    depreciation_ratio: Optional[float] = None

    # --------------------------------------------------------
    # Underlying profitability
    # --------------------------------------------------------

    underlying_pbt: Optional[float] = None

    exceptional_adjusted_pat: Optional[float] = None

    # --------------------------------------------------------
    # Leverage
    # --------------------------------------------------------

    debt_equity_ratio: Optional[float] = None
    debt_service_coverage_ratio: Optional[float] = None
    interest_service_coverage_ratio: Optional[float] = None

    # --------------------------------------------------------
    # Quality flags
    # --------------------------------------------------------

    exceptional_item_dominant: bool = False
    other_income_dominant: bool = False
    high_finance_cost: bool = False


# ============================================================
# Feature Calculator
# ============================================================


class FinancialFeatureCalculator:
    """
    Calculates derived financial features from CompanyResult.

    Input:
        CompanyResult

    Output:
        FinancialFeatures
    """

    def calculate(
        self,
        company_result,
        period: str = "quarterly",
    ) -> FinancialFeatures:

        financial_period = getattr(
            company_result,
            period,
            None,
        )

        if financial_period is None:

            raise ValueError(
                f"Financial period '{period}' "
                f"does not exist in CompanyResult."
            )

        metrics = financial_period.metrics

        # ----------------------------------------------------
        # Basic metrics
        # ----------------------------------------------------

        revenue = self._get(metrics, "revenue")

        other_income = self._get(
            metrics,
            "other_income",
        )

        total_income = self._get(
            metrics,
            "total_income",
        )

        total_expenses = self._get(
            metrics,
            "total_expenses",
        )

        finance_cost = self._get(
            metrics,
            "finance_cost",
        )

        depreciation = self._get(
            metrics,
            "depreciation",
        )

        pbt_before_exceptional = self._get(
            metrics,
            "pbt_before_exceptional",
        )

        exceptional_items = self._get(
            metrics,
            "exceptional_items",
        )

        pbt = self._get(
            metrics,
            "pbt",
        )

        pat = self._get(
            metrics,
            "pat",
        )

        eps_basic = self._get(
            metrics,
            "eps_basic",
        )

        # ----------------------------------------------------
        # Derived values
        # ----------------------------------------------------

        underlying_pbt = pbt_before_exceptional

        exceptional_adjusted_pat = self._calculate_adjusted_pat(
            pat=pat,
            exceptional_items=exceptional_items,
        )

        # ----------------------------------------------------
        # Build feature object
        # ----------------------------------------------------

        features = FinancialFeatures(

            # Basic
            revenue=revenue,
            other_income=other_income,
            total_income=total_income,

            total_expenses=total_expenses,
            finance_cost=finance_cost,
            depreciation=depreciation,

            pbt_before_exceptional=pbt_before_exceptional,
            exceptional_items=exceptional_items,
            pbt=pbt,
            pat=pat,

            eps_basic=eps_basic,

            # Margins
            pbt_margin=self._safe_ratio(
                pbt,
                revenue,
            ),

            pat_margin=self._safe_ratio(
                pat,
                revenue,
            ),

            # Income quality
            other_income_ratio=self._safe_ratio(
                other_income,
                revenue,
            ),

            exceptional_item_ratio=self._safe_ratio(
                exceptional_items,
                revenue,
            ),

            exceptional_item_to_pbt_before_exceptional=self._safe_ratio(
                exceptional_items,
                pbt_before_exceptional,
            ),

            reported_pbt_to_underlying_pbt=self._safe_ratio(
                pbt,
                underlying_pbt,
            ),

            reported_pat_to_underlying_pbt=self._safe_ratio(
                pat,
                underlying_pbt,
            ),

            # Expense structure
            expense_ratio=self._safe_ratio(
                total_expenses,
                revenue,
            ),

            finance_cost_ratio=self._safe_ratio(
                finance_cost,
                revenue,
            ),

            depreciation_ratio=self._safe_ratio(
                depreciation,
                revenue,
            ),

            # Underlying profitability
            underlying_pbt=underlying_pbt,

            exceptional_adjusted_pat=exceptional_adjusted_pat,

            # Leverage
            debt_equity_ratio=self._get(
                metrics,
                "debt_equity_ratio",
            ),

            debt_service_coverage_ratio=self._get(
                metrics,
                "debt_service_coverage_ratio",
            ),

            interest_service_coverage_ratio=self._get(
                metrics,
                "interest_service_coverage_ratio",
            ),
        )

        # ----------------------------------------------------
        # Quality flags
        # ----------------------------------------------------

        features.exceptional_item_dominant = (
            self._is_exceptional_item_dominant(
                features
            )
        )

        features.other_income_dominant = (
            self._is_other_income_dominant(
                features
            )
        )

        features.high_finance_cost = (
            self._is_high_finance_cost(
                features
            )
        )

        return features

    # ========================================================
    # Helpers
    # ========================================================

    @staticmethod
    def _get(
        metrics: dict,
        key: str,
    ) -> Optional[float]:

        value = metrics.get(key)

        if value is None:
            return None

        return float(value)

    @staticmethod
    def _safe_ratio(
        numerator: Optional[float],
        denominator: Optional[float],
    ) -> Optional[float]:

        if numerator is None:
            return None

        if denominator is None:
            return None

        if denominator == 0:
            return None

        return numerator / denominator

    @staticmethod
    def _calculate_adjusted_pat(
        pat: Optional[float],
        exceptional_items: Optional[float],
    ) -> Optional[float]:

        if pat is None:
            return None

        if exceptional_items is None:
            return pat

        return pat - exceptional_items

    # ========================================================
    # Quality Detection
    # ========================================================

    @staticmethod
    def _is_exceptional_item_dominant(
        features: FinancialFeatures,
    ) -> bool:

        ratio = (
            features.exceptional_item_to_pbt_before_exceptional
        )

        if ratio is None:
            return False

        return abs(ratio) >= 1.0

    @staticmethod
    def _is_other_income_dominant(
        features: FinancialFeatures,
    ) -> bool:

        ratio = features.other_income_ratio

        if ratio is None:
            return False

        # Other income >= 50% of operating revenue
        return abs(ratio) >= 0.50

    @staticmethod
    def _is_high_finance_cost(
        features: FinancialFeatures,
    ) -> bool:

        ratio = features.finance_cost_ratio

        if ratio is None:
            return False

        # Finance cost >= 10% of revenue
        return abs(ratio) >= 0.10

    # ========================================================
    # JSON
    # ========================================================

    @staticmethod
    def to_dict(
        features: FinancialFeatures,
    ) -> dict:

        return asdict(features)