from __future__ import annotations

from app.models import CalcResult
from app.registry import registry


def compute_mao(strategy_name: str, arv_value: float | None, property_data: dict, params: dict) -> CalcResult:
    strategy = registry.get("mao", strategy_name)
    return strategy(arv_value=arv_value, property_data=property_data, params=params)
