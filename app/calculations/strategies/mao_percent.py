from __future__ import annotations

from app.models import CalcResult
from app.registry import register_mao


@register_mao("percent_of_arv")
def mao_percent_of_arv(*, arv_value: float | None, property_data: dict, params: dict) -> CalcResult:
    if arv_value is None:
        return CalcResult(value=None, warnings=["MAO_UNKNOWN_NO_ARV"])

    percent = float(params.get("percent", 0.15))
    county = property_data.get("county")
    overrides = params.get("county_overrides", {})
    if county in overrides:
        percent = float(overrides[county])

    return CalcResult(value=float(arv_value * percent), warnings=[])
