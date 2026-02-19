from __future__ import annotations

from statistics import median

from app.models import CalcResult
from app.registry import register_arv


@register_arv("median_ppsqft")
def arv_median_ppsqft(*, property_data: dict, findings: dict, params: dict) -> CalcResult:
    comps_ppsqft = findings.get("comps_ppsqft", [])
    target_sqft = findings.get("target_build_sqft")

    if not comps_ppsqft or not isinstance(target_sqft, (int, float)):
        return CalcResult(value=None, warnings=["ARV_UNKNOWN_NO_COMPS"])

    value = float(median(comps_ppsqft) * target_sqft)
    return CalcResult(value=value, warnings=[])
