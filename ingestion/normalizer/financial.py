from dataclasses import dataclass, asdict
from typing import Optional


# ---------------------------------------------------------
# Mapping XBRL concepts → canonical financial metrics
# ---------------------------------------------------------

CONCEPT_MAP = {

    "RevenueFromOperations":
        "revenue",

    "OtherIncome":
        "other_income",

    "Income":
        "total_income",

    "CostOfMaterialsConsumed":
        "cost_of_materials",

    "PurchasesOfStockInTrade":
        "purchases",

    "ChangesInInventoriesOfFinishedGoodsWorkInProgressAndStockInTrade":
        "inventory_change",

    "EmployeeBenefitExpense":
        "employee_expense",

    "FinanceCosts":
        "finance_cost",

    "DepreciationDepletionAndAmortisationExpense":
        "depreciation",

    "OtherExpenses":
        "other_expenses",

    "Expenses":
        "total_expenses",

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

    "ComprehensiveIncomeForThePeriod":
        "comprehensive_income",

    "PaidUpValueOfEquityShareCapital":
        "paid_up_equity",

    "FaceValueOfEquityShareCapital":
        "face_value",

    "BasicEarningsLossPerShareFromContinuingOperations":
        "eps_basic",

    "DilutedEarningsLossPerShareFromContinuingOperations":
        "eps_diluted",

    "DebtEquityRatio":
        "debt_equity_ratio",

    "DebtServiceCoverageRatio":
        "debt_service_coverage_ratio",

    "InterestServiceCoverageRatio":
        "interest_service_coverage_ratio",
}


@dataclass
class NormalizedFact:

    company_symbol: Optional[str]

    metric: str

    value: Optional[float]

    unit: Optional[str]

    period_start: Optional[str]

    period_end: Optional[str]

    period_type: Optional[str]

    context_id: Optional[str]

    dimensions: Optional[dict]

    decimals: Optional[str]