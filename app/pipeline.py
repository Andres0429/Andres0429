from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone

from app.agents.browsing_agent import BrowsingAgent
from app.agents.structuring_agent import StructuringAgent
from app.calculations.arv import compute_arv
from app.calculations.mao import compute_mao
import app.calculations.strategies  # noqa: F401 ensure registration
from app.config_loader import load_and_validate
from app.models import PropertyInput
from app.storage import Storage


def compute_target_build_sqft(max_buildable_sqft: float | None, cap: int = 1600) -> float | None:
    if max_buildable_sqft is None:
        return float(cap)
    return float(min(max_buildable_sqft, cap))


def _property_key(row: dict) -> str:
    value = f"{row.get('address_line1','')}|{row.get('city','')}|{row.get('state','TN')}|{row.get('zip','')}"
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def run_pipeline(input_csv: str, output_csv: str, fields_config: str, calc_config: str, sources_config: str, cache_db: str):
    cfg = load_and_validate(fields_config, calc_config, sources_config)
    storage = Storage(cache_db)
    browser = BrowsingAgent()
    structurer = StructuringAgent()

    output_columns = [f.output_column for f in cfg.fields.fields]
    meta_columns = ["property_id", "status", "warnings", "processed_at_utc", "config_hash", "session_id"]

    with open(input_csv, "r", encoding="utf-8") as fin, open(output_csv, "w", encoding="utf-8", newline="") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=output_columns + meta_columns)
        writer.writeheader()

        for idx, row in enumerate(reader, start=1):
            property_id = row.get("property_id") or f"row_{idx}"
            normalized = {
                "property_id": property_id,
                "address_line1": row["address_line1"],
                "city": row["city"],
                "state": row.get("state", "TN"),
                "zip": row.get("zip"),
                "county": row.get("county"),
            }
            prop = PropertyInput.model_validate(normalized)
            key = _property_key(normalized)

            cached = storage.get_cache(key, cfg.config_hash)
            if cached:
                writer.writerow(cached)
                continue

            raw = browser.run_property_session(prop, cfg.sources.default)
            structured = structurer.structure(raw, cfg.fields, cfg.config_hash)

            values = {name: result.value for name, result in structured.fields.items()}
            max_buildable = values.get("max_buildable_sqft")
            if isinstance(max_buildable, str):
                max_buildable = None

            target = compute_target_build_sqft(max_buildable, cfg.calculations.target_cap_sqft)
            structured.fields["target_build_sqft"] = {
                "value": target,
                "status": "OK" if target is not None else "UNKNOWN",
                "source": "calculation",
                "evidence_refs": [],
            }

            findings_for_calc = {
                "target_build_sqft": target,
                "comps_ppsqft": [220.0, 210.0, 230.0],
            }
            arv = compute_arv(cfg.calculations.arv.strategy, normalized, findings_for_calc, cfg.calculations.arv.params)
            mao = compute_mao(cfg.calculations.mao.strategy, arv.value, normalized, cfg.calculations.mao.params)

            if arv.value is not None:
                values["arv_estimate_usd"] = arv.value
            else:
                values["arv_estimate_usd"] = "UNKNOWN"
            if mao.value is not None:
                values["max_offer_usd"] = mao.value
            else:
                values["max_offer_usd"] = "UNKNOWN"
            values["target_build_sqft"] = target

            warnings = structured.warnings + arv.warnings + mao.warnings
            status = "OK" if not warnings else "PARTIAL"

            out = {f.output_column: values.get(f.name, f.default) for f in cfg.fields.fields}
            out.update(
                {
                    "property_id": property_id,
                    "status": status,
                    "warnings": json.dumps(warnings),
                    "processed_at_utc": datetime.now(timezone.utc).isoformat(),
                    "config_hash": cfg.config_hash,
                    "session_id": raw.session_id,
                }
            )

            storage.set_cache(key, cfg.config_hash, out)
            writer.writerow(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--fields-config", required=True)
    parser.add_argument("--calc-config", required=True)
    parser.add_argument("--sources-config", required=True)
    parser.add_argument("--cache-db", required=True)
    args = parser.parse_args()

    run_pipeline(
        input_csv=args.input,
        output_csv=args.output,
        fields_config=args.fields_config,
        calc_config=args.calc_config,
        sources_config=args.sources_config,
        cache_db=args.cache_db,
    )


if __name__ == "__main__":
    main()
