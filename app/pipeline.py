from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
from datetime import datetime, timezone

from app.agents.browsing_agent import BrowsingAgent
from app.agents.structuring_agent import StructuringAgent
from app.calculations.arv import compute_arv
from app.calculations.mao import compute_mao
import app.calculations.strategies  # noqa: F401 ensure registration
from app.config_loader import load_and_validate
from app.models import FieldResult, PropertyInput
from app.storage import Storage

logger = logging.getLogger(__name__)


def compute_target_build_sqft(max_buildable_sqft: float | None, cap: int = 1600) -> float | None:
    if max_buildable_sqft is None:
        return float(cap)
    return float(min(max_buildable_sqft, cap))


def _property_key(row: dict) -> str:
    value = f"{row.get('address_line1','')}|{row.get('city','')}|{row.get('state','TN')}|{row.get('zip','')}"
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def _extract_numeric_finding(raw, field_name: str) -> float | None:
    for finding in raw.findings:
        if finding.field_name != field_name:
            continue
        if isinstance(finding.raw_value, (int, float)):
            return float(finding.raw_value)
    return None


def _extract_comps_ppsqft(raw) -> list[float]:
    values: list[float] = []
    for finding in raw.findings:
        if finding.field_name != "comp_ppsqft":
            continue
        if isinstance(finding.raw_value, (int, float)):
            values.append(float(finding.raw_value))
    return values


def run_pipeline(
    input_csv: str,
    output_csv: str,
    fields_config: str,
    calc_config: str,
    sources_config: str,
    cache_db: str,
    use_cache: bool = True,
):
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

            if use_cache:
                cached = storage.get_cache(key, cfg.config_hash)
                if cached:
                    logger.info("cache_hit property_id=%s key=%s", property_id, key[:12])
                    writer.writerow(cached)
                    continue
                logger.info("cache_miss property_id=%s key=%s", property_id, key[:12])
            else:
                logger.info("cache_disabled property_id=%s", property_id)

            raw = browser.run_property_session(prop, cfg.sources.default)
            structured = structurer.structure(raw, cfg.fields, cfg.config_hash)

            max_buildable = _extract_numeric_finding(raw, "max_buildable_sqft")
            target = compute_target_build_sqft(max_buildable, cfg.calculations.target_cap_sqft)
            structured.fields["target_build_sqft"] = FieldResult(
                value=target,
                status="OK" if target is not None else "UNKNOWN",
                source="calculation",
                evidence_refs=[],
            )

            findings_for_calc = {
                "target_build_sqft": target,
                "comps_ppsqft": _extract_comps_ppsqft(raw),
            }
            arv = compute_arv(cfg.calculations.arv.strategy, normalized, findings_for_calc, cfg.calculations.arv.params)
            mao = compute_mao(cfg.calculations.mao.strategy, arv.value, normalized, cfg.calculations.mao.params)

            if arv.value is not None:
                structured.fields["arv_estimate_usd"] = FieldResult(
                    value=arv.value,
                    status="OK",
                    source=f"strategy:{cfg.calculations.arv.strategy}",
                )
            if mao.value is not None:
                structured.fields["max_offer_usd"] = FieldResult(
                    value=mao.value,
                    status="OK",
                    source=f"strategy:{cfg.calculations.mao.strategy}",
                )

            warnings = structured.warnings + arv.warnings + mao.warnings
            status = "OK" if not warnings else "PARTIAL"

            values = {name: result.value for name, result in structured.fields.items()}
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

            if use_cache:
                storage.set_cache(key, cfg.config_hash, out)
            writer.writerow(out)
            logger.info("processed property_id=%s status=%s warnings=%d", property_id, status, len(warnings))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--fields-config", required=True)
    parser.add_argument("--calc-config", required=True)
    parser.add_argument("--sources-config", required=True)
    parser.add_argument("--cache-db", required=True)
    parser.add_argument("--no-cache", action="store_true", help="Disable read/write cache for this run")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    run_pipeline(
        input_csv=args.input,
        output_csv=args.output,
        fields_config=args.fields_config,
        calc_config=args.calc_config,
        sources_config=args.sources_config,
        cache_db=args.cache_db,
        use_cache=not args.no_cache,
    )


if __name__ == "__main__":
    main()
