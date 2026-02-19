import json

import pytest

import app.calculations.strategies  # noqa: F401 ensure plugins are registered
from app.config_loader import load_and_validate


def test_config_loader_success():
    cfg = load_and_validate("config/fields.yaml", "config/calculations.yaml", "config/sources.yaml")
    assert cfg.config_hash.startswith("sha256:")
    assert cfg.calculations.target_cap_sqft == 1600


def test_config_loader_dependency_error(tmp_path):
    fields = tmp_path / "fields.yaml"
    fields.write_text(
        json.dumps(
            {
                "fields": [
                    {
                        "name": "a",
                        "output_column": "a",
                        "dtype": "float",
                        "required": True,
                        "default": "UNKNOWN",
                        "extraction_hints": {"keywords": [], "selectors": [], "evidence_required": False},
                        "preferred_sources": [],
                        "validators": {},
                        "dependencies": ["b"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown field 'b'"):
        load_and_validate(str(fields), "config/calculations.yaml", "config/sources.yaml")


def test_config_loader_unknown_strategy(tmp_path):
    calc = tmp_path / "calc.yaml"
    calc.write_text(
        json.dumps(
            {
                "target_cap_sqft": 1600,
                "arv": {"strategy": "does_not_exist", "params": {}},
                "mao": {"strategy": "percent_of_arv", "params": {"percent": 0.15}},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not registered"):
        load_and_validate("config/fields.yaml", str(calc), "config/sources.yaml")
