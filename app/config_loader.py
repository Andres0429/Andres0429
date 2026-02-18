from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from app import models
from app.registry import registry


@dataclass
class LoadedConfig:
    fields: models.FieldsConfig
    calculations: models.CalculationsConfig
    sources: models.SourcesConfig
    config_hash: str


def _load_yaml(path: Path) -> dict:
    # YAML parser dependency is intentionally avoided for portability in this environment.
    # JSON is valid YAML, so config files are authored in JSON syntax with .yaml extension.
    with path.open("r", encoding="utf-8") as f:
        return json.loads(f.read() or "{}")


def _compute_hash(payload: dict) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_and_validate(fields_path: str, calculations_path: str, sources_path: str) -> LoadedConfig:
    fields_raw = _load_yaml(Path(fields_path))
    calc_raw = _load_yaml(Path(calculations_path))
    sources_raw = _load_yaml(Path(sources_path))

    fields = models.FieldsConfig.model_validate(fields_raw)
    calculations = models.CalculationsConfig.model_validate(calc_raw)
    sources = models.SourcesConfig.model_validate(sources_raw)

    field_names = {f.name for f in fields.fields}
    for field in fields.fields:
        for dep in field.dependencies:
            if dep not in field_names:
                raise ValueError(f"fields.{field.name}.dependencies references unknown field '{dep}'")

    if not registry.has("arv", calculations.arv.strategy):
        raise ValueError(f"calculations.arv.strategy '{calculations.arv.strategy}' not registered")
    if not registry.has("mao", calculations.mao.strategy):
        raise ValueError(f"calculations.mao.strategy '{calculations.mao.strategy}' not registered")

    source_names = set()
    for _, source_list in sources.default.items():
        source_names.update(source_list)

    for field in fields.fields:
        for source in field.preferred_sources:
            if source_names and source not in source_names:
                raise ValueError(
                    f"fields.{field.name}.preferred_sources references unknown source '{source}' "
                    "(missing from sources.default)"
                )

    config_hash = _compute_hash({"fields": fields_raw, "calculations": calc_raw, "sources": sources_raw})

    return LoadedConfig(fields=fields, calculations=calculations, sources=sources, config_hash=config_hash)
