from dataclasses import dataclass, field

from backend.core.logging import get_logger
from backend.domain.ports import RuleResult

logger = get_logger(__name__)


@dataclass
class BusinessRule:
    name: str = ""
    description: str = ""
    hard_block: bool = False

    def evaluate(self, features: dict[str, float]) -> RuleResult:
        raise NotImplementedError


@dataclass
class IncomeTooHighRule(BusinessRule):
    max_income: float = 50000.0

    def __post_init__(self):
        self.name = "income_too_high"
        self.description = f"Monthly income exceeds AED {self.max_income:,.0f}"

    def evaluate(self, features: dict[str, float]) -> RuleResult:
        income = features.get("monthly_income", 0.0)
        passed = income <= self.max_income
        return RuleResult(
            rule_name=self.name,
            passed=passed,
            details=None if passed else f"Monthly income AED {income:,.2f} exceeds maximum AED {self.max_income:,.0f}",
        )


@dataclass
class AssetThresholdRule(BusinessRule):
    max_assets: float = 500000.0

    def __post_init__(self):
        self.name = "asset_threshold"
        self.description = f"Total assets exceed AED {self.max_assets:,.0f}"

    def evaluate(self, features: dict[str, float]) -> RuleResult:
        assets = features.get("total_assets", 0.0)
        passed = assets <= self.max_assets
        return RuleResult(
            rule_name=self.name,
            passed=passed,
            details=None if passed else f"Total assets AED {assets:,.2f} exceed maximum AED {self.max_assets:,.0f}",
        )


@dataclass
class DebtBurdenRule(BusinessRule):
    max_ratio: float = 3.0

    def __post_init__(self):
        self.name = "debt_burden"
        self.description = f"Liability-to-income ratio exceeds {self.max_ratio}x"

    def evaluate(self, features: dict[str, float]) -> RuleResult:
        ratio = features.get("liability_to_income_ratio", 0.0)
        passed = ratio <= self.max_ratio
        return RuleResult(
            rule_name=self.name,
            passed=passed,
            details=None if passed else f"Debt ratio {ratio:.2f}x exceeds maximum {self.max_ratio}x",
        )


@dataclass
class MinimumIncomeRule(BusinessRule):
    min_income: float = 1000.0

    def __post_init__(self):
        self.name = "minimum_income"
        self.description = f"Monthly income below AED {self.min_income:,.0f}"

    def evaluate(self, features: dict[str, float]) -> RuleResult:
        income = features.get("monthly_income", 0.0)
        passed = income >= self.min_income
        return RuleResult(
            rule_name=self.name,
            passed=passed,
            details=None if passed else f"Monthly income AED {income:,.2f} below minimum AED {self.min_income:,.0f}",
        )


@dataclass
class DocumentCompletenessRule(BusinessRule):
    min_documents: int = 1

    def __post_init__(self):
        self.name = "document_completeness"
        self.description = f"Fewer than {self.min_documents} supporting documents"

    def evaluate(self, features: dict[str, float]) -> RuleResult:
        docs = int(features.get("num_documents", 0))
        passed = docs >= self.min_documents
        return RuleResult(
            rule_name=self.name,
            passed=passed,
            details=None if passed else f"Only {docs} document(s) provided, minimum is {self.min_documents}",
        )


HARD_RULES: list[BusinessRule] = [
    IncomeTooHighRule(hard_block=True),
    AssetThresholdRule(hard_block=True),
    DebtBurdenRule(hard_block=True),
    MinimumIncomeRule(hard_block=True),
    DocumentCompletenessRule(hard_block=False),
]

SOFT_RULES: list[BusinessRule] = [
    DocumentCompletenessRule(hard_block=False),
]


async def evaluate_all_rules(features: dict[str, float]) -> list[RuleResult]:
    results = []
    for rule in HARD_RULES:
        result = rule.evaluate(features)
        results.append(result)
        logger.debug(f"Rule '{rule.name}': passed={result.passed}")
    return results


async def has_hard_blockers(results: list[RuleResult]) -> bool:
    return any(not r.passed for r in results if _is_hard_rule(r.rule_name))


def _is_hard_rule(name: str) -> bool:
    hard_names = {r.name for r in HARD_RULES if r.hard_block}
    return name in hard_names
