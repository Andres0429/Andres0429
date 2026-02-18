from __future__ import annotations

from app.models import CalcResult
from app.registry import register_arv


@register_arv("regression_simple")
def arv_regression_simple(*, property_data: dict, findings: dict, params: dict) -> CalcResult:
    # MVP placeholder: fallback to median_ppsqft-like output when slope/intercept absent.
    slope = params.get("slope")
    intercept = params.get("intercept", 0)
    target_sqft = findings.get("target_build_sqft")

    if slope is None or not isinstance(target_sqft, (int, float)):
        return CalcResult(value=None, warnings=["ARV_UNKNOWN_REGRESSION_INPUTS"])

    return CalcResult(value=float(slope * target_sqft + intercept), warnings=[])
