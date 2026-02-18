from __future__ import annotations

from app.models import CalcResult
from app.registry import registry


def compute_arv(strategy_name: str, property_data: dict, findings: dict, params: dict) -> CalcResult:
    strategy = registry.get("arv", strategy_name)
    return strategy(property_data=property_data, findings=findings, params=params)
