import pytest

from app.calculations.mao import compute_mao
import app.calculations.strategies  # noqa: F401 ensure plugin registration


def test_mao_percent_default():
    result = compute_mao("percent_of_arv", 300000, {"county": "Other"}, {"percent": 0.15})
    assert result.value == pytest.approx(45000)


def test_mao_percent_county_override():
    result = compute_mao(
        "percent_of_arv",
        300000,
        {"county": "Davidson"},
        {"percent": 0.15, "county_overrides": {"Davidson": 0.14}},
    )
    assert result.value == pytest.approx(42000)
