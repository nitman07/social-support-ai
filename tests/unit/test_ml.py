from backend.ml.rules import AssetThresholdRule, DebtBurdenRule, IncomeTooHighRule, MinimumIncomeRule


def _make_features(overrides: dict | None = None) -> dict[str, float]:
    base = {
        "monthly_income": 5000.0,
        "family_size": 4,
        "years_employed": 5,
        "total_assets": 100000.0,
        "total_liabilities": 50000.0,
        "liability_to_income_ratio": 2.0,
        "has_inconsistencies": 0.0,
        "num_documents": 3,
    }
    if overrides:
        base.update(overrides)
    return base


class TestRules:
    def test_income_too_high_passes(self):
        rule = IncomeTooHighRule()
        result = rule.evaluate(_make_features({"monthly_income": 25000.0}))
        assert result.passed is True

    def test_income_too_high_fails(self):
        rule = IncomeTooHighRule()
        result = rule.evaluate(_make_features({"monthly_income": 60000.0}))
        assert result.passed is False

    def test_asset_threshold_passes(self):
        rule = AssetThresholdRule()
        result = rule.evaluate(_make_features({"total_assets": 200000.0}))
        assert result.passed is True

    def test_asset_threshold_fails(self):
        rule = AssetThresholdRule()
        result = rule.evaluate(_make_features({"total_assets": 600000.0}))
        assert result.passed is False

    def test_debt_burden_passes(self):
        rule = DebtBurdenRule()
        result = rule.evaluate(_make_features({"total_liabilities": 20000.0}))
        assert result.passed is True

    def test_minimum_income_passes(self):
        rule = MinimumIncomeRule()
        result = rule.evaluate(_make_features({"monthly_income": 2000.0}))
        assert result.passed is True

    def test_minimum_income_fails(self):
        rule = MinimumIncomeRule()
        result = rule.evaluate(_make_features({"monthly_income": 500.0}))
        assert result.passed is False
