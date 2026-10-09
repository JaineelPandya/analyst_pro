from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional, Sequence


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class HistoricalMetricComparison:
    metric: str

    current_value: Optional[float]
    previous_value: Optional[float]

    absolute_change: Optional[float]
    percentage_change: Optional[float]

    direction: Optional[str]


@dataclass
class HistoricalComparisonResult:
    comparison_type: str

    current_period: str
    previous_period: Optional[str]

    metrics: list[HistoricalMetricComparison]

    summary: dict


# ============================================================
# HISTORICAL COMPARISON ENGINE
# ============================================================

class HistoricalComparisonEngine:
    """
    Compares financial periods and identifies meaningful
    historical changes.

    This is a deterministic baseline layer.

    It does NOT make investment recommendations.
    """

    # Metrics that are useful for historical comparison.
    DEFAULT_METRICS = [
        "revenue",
        "other_income",
        "total_income",
        "total_expenses",
        "finance_cost",
        "depreciation",
        "pbt_before_exceptional",
        "exceptional_items",
        "pbt",
        "pat",
        "eps_basic",
    ]

    def compare(
        self,
        current_period,
        previous_period,
        comparison_type: str = "period_over_period",
        metrics: Optional[Sequence[str]] = None,
    ) -> HistoricalComparisonResult:
        """
        Compare two FinancialPeriod objects.

        Example:
            engine.compare(
                current_period,
                previous_period,
                comparison_type="QoQ"
            )
        """

        metric_names = list(metrics or self.DEFAULT_METRICS)

        comparisons = []

        for metric in metric_names:

            current_value = self._get_metric(
                current_period,
                metric
            )

            previous_value = self._get_metric(
                previous_period,
                metric
            )

            absolute_change = None
            percentage_change = None
            direction = None

            if current_value is not None and previous_value is not None:

                absolute_change = current_value - previous_value

                percentage_change = self._percentage_change(
                    previous_value,
                    current_value
                )

                direction = self._direction(
                    absolute_change
                )

            comparisons.append(
                HistoricalMetricComparison(
                    metric=metric,
                    current_value=current_value,
                    previous_value=previous_value,
                    absolute_change=absolute_change,
                    percentage_change=percentage_change,
                    direction=direction,
                )
            )

        summary = self._build_summary(comparisons)

        return HistoricalComparisonResult(
            comparison_type=comparison_type,
            current_period=self._period_label(current_period),
            previous_period=self._period_label(previous_period),
            metrics=comparisons,
            summary=summary,
        )

    # ========================================================
    # METRIC ACCESS
    # ========================================================

    @staticmethod
    def _get_metric(period, metric: str) -> Optional[float]:

        if period is None:
            return None

        metrics = getattr(period, "metrics", None)

        if not isinstance(metrics, dict):
            return None

        value = metrics.get(metric)

        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    # ========================================================
    # CALCULATIONS
    # ========================================================

    @staticmethod
    def _percentage_change(
        previous_value: float,
        current_value: float,
    ) -> Optional[float]:

        if previous_value == 0:

            if current_value == 0:
                return 0.0

            return None

        return (
            (current_value - previous_value)
            / abs(previous_value)
        ) * 100.0

    @staticmethod
    def _direction(
        absolute_change: float,
    ) -> str:

        if absolute_change > 0:
            return "increase"

        if absolute_change < 0:
            return "decrease"

        return "unchanged"

    # ========================================================
    # PERIOD LABEL
    # ========================================================

    @staticmethod
    def _period_label(period) -> str:

        if period is None:
            return "unknown"

        period_type = getattr(
            period,
            "period_type",
            "unknown"
        )

        start_date = getattr(
            period,
            "start_date",
            None
        )

        end_date = getattr(
            period,
            "end_date",
            None
        )

        instant = getattr(
            period,
            "instant",
            None
        )

        if start_date and end_date:
            return (
                f"{period_type}: "
                f"{start_date} -> {end_date}"
            )

        if instant:
            return (
                f"{period_type}: "
                f"{instant}"
            )

        return str(period_type)

    # ========================================================
    # SUMMARY
    # ========================================================

    @staticmethod
    def _build_summary(
        comparisons: list[HistoricalMetricComparison],
    ) -> dict:

        increases = []
        decreases = []
        unchanged = []

        for comparison in comparisons:

            if comparison.direction == "increase":
                increases.append(comparison.metric)

            elif comparison.direction == "decrease":
                decreases.append(comparison.metric)

            elif comparison.direction == "unchanged":
                unchanged.append(comparison.metric)

        largest_increase = None
        largest_decrease = None

        valid_percentage_changes = [
            comparison
            for comparison in comparisons
            if comparison.percentage_change is not None
        ]

        if valid_percentage_changes:

            largest_increase = max(
                valid_percentage_changes,
                key=lambda x: x.percentage_change
            )

            largest_decrease = min(
                valid_percentage_changes,
                key=lambda x: x.percentage_change
            )

        return {
            "metrics_increased": increases,
            "metrics_decreased": decreases,
            "metrics_unchanged": unchanged,
            "largest_percentage_increase": (
                {
                    "metric": largest_increase.metric,
                    "percentage_change": (
                        largest_increase.percentage_change
                    ),
                }
                if largest_increase
                else None
            ),
            "largest_percentage_decrease": (
                {
                    "metric": largest_decrease.metric,
                    "percentage_change": (
                        largest_decrease.percentage_change
                    ),
                }
                if largest_decrease
                else None
            ),
        }

    # ========================================================
    # SERIALIZATION
    # ========================================================

    @staticmethod
    def to_dict(
        result: HistoricalComparisonResult,
    ) -> dict:

        return asdict(result) 