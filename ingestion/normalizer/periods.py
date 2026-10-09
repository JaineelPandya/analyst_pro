from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


# ============================================================
# Data Models
# ============================================================

@dataclass
class PeriodClassification:
    context_id: str

    period_type: str
    # quarterly | ytd | annual | instant | other

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    instant: Optional[str] = None

    duration_days: Optional[int] = None
    duration_months: Optional[float] = None

    fiscal_year: Optional[str] = None
    quarter: Optional[str] = None

    confidence: str = "high"

    warnings: list[str] | None = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


# ============================================================
# Period Classifier
# ============================================================

class PeriodClassifier:
    """
    Classifies raw XBRL contexts into canonical financial periods.

    Important:
    - Does NOT rely on context IDs such as OneD/FourD.
    - Uses actual start/end dates.
    - Keeps instant contexts separate.
    """

    def classify(self, context) -> PeriodClassification:

        if context.period_type == "instant":
            return self._classify_instant(context)

        if context.period_type == "duration":
            return self._classify_duration(context)

        return PeriodClassification(
            context_id=context.context_id,
            period_type="other",
            confidence="low",
            warnings=["UNKNOWN_PERIOD_TYPE"],
        )

    # --------------------------------------------------------
    # Instant
    # --------------------------------------------------------

    def _classify_instant(self, context):

        return PeriodClassification(
            context_id=context.context_id,
            period_type="instant",
            instant=context.instant,
            confidence="high",
            warnings=[],
        )

    # --------------------------------------------------------
    # Duration
    # --------------------------------------------------------

    def _classify_duration(self, context):

        if not context.start_date or not context.end_date:
            return PeriodClassification(
                context_id=context.context_id,
                period_type="other",
                confidence="low",
                warnings=["MISSING_DURATION_DATES"],
            )

        start = self._parse_date(context.start_date)
        end = self._parse_date(context.end_date)

        if start > end:
            return PeriodClassification(
                context_id=context.context_id,
                period_type="other",
                start_date=context.start_date,
                end_date=context.end_date,
                confidence="low",
                warnings=["START_DATE_AFTER_END_DATE"],
            )

        duration_days = (end - start).days
        duration_months = self._months_between(start, end)

        fiscal_year = self._infer_fiscal_year(start, end)

        quarter = self._infer_quarter(start, end)

        warnings = []

        period_type = self._classify_duration_type(
            start=start,
            end=end,
            duration_months=duration_months,
        )

        return PeriodClassification(
            context_id=context.context_id,
            period_type=period_type,
            start_date=context.start_date,
            end_date=context.end_date,
            duration_days=duration_days,
            duration_months=duration_months,
            fiscal_year=fiscal_year,
            quarter=quarter,
            confidence="high",
            warnings=warnings,
        )

    # ========================================================
    # Duration Classification
    # ========================================================

    def _classify_duration_type(
        self,
        start: date,
        end: date,
        duration_months: float,
    ) -> str:

        # ---------------------------------------------
        # Indian financial year:
        # 1 April → 31 March
        # ---------------------------------------------

        fy_start = date(
            start.year if start.month >= 4 else start.year - 1,
            4,
            1,
        )

        # Exact FY
        if start == fy_start:

            if end.month == 3 and end.day in (30, 31):
                return "annual"

            # 6-month / 9-month cumulative periods
            if end.month == 9:
                return "ytd"

            if end.month == 12:
                return "ytd"

            if end.month in (6,):
                return "ytd"

        # ---------------------------------------------
        # Quarterly duration
        # ---------------------------------------------

        if 2.5 <= duration_months <= 3.5:
            return "quarterly"

        # ---------------------------------------------
        # Generic YTD
        # ---------------------------------------------

        if 5.5 <= duration_months <= 9.5:
            return "ytd"

        # ---------------------------------------------
        # Generic annual
        # ---------------------------------------------

        if 11.0 <= duration_months <= 12.5:
            return "annual"

        return "other"

    # ========================================================
    # Quarter Inference
    # ========================================================

    def _infer_quarter(
        self,
        start: date,
        end: date,
    ) -> Optional[str]:

        # Indian FY quarters
        #
        # Q1: Apr-Jun
        # Q2: Jul-Sep
        # Q3: Oct-Dec
        # Q4: Jan-Mar

        quarter_ranges = {
            1: (4, 6),
            2: (7, 9),
            3: (10, 12),
            4: (1, 3),
        }

        for quarter, (start_month, end_month) in quarter_ranges.items():

            if (
                start.month == start_month
                and end.month == end_month
            ):
                return f"Q{quarter}"

        return None

    # ========================================================
    # Fiscal Year
    # ========================================================

    def _infer_fiscal_year(
        self,
        start: date,
        end: date,
    ) -> Optional[str]:

        # Indian FY is Apr-Mar.
        #
        # Apr 2024 → Mar 2025
        # becomes FY2025

        if start.month >= 4:

            fy_end_year = start.year + 1

        else:

            fy_end_year = start.year

        return f"FY{fy_end_year}"

    # ========================================================
    # Date Helpers
    # ========================================================

    @staticmethod
    def _parse_date(value: str) -> date:

        return date.fromisoformat(value)

    @staticmethod
    def _months_between(
        start: date,
        end: date,
    ) -> float:

        days = (end - start).days

        # Approximate months.
        # Used only for classification.
        return days / 30.4375