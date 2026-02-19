from __future__ import annotations

from app.registry import register_extractor


@register_extractor("official_county")
def extract_official_county(payload: dict) -> dict:
    return payload
