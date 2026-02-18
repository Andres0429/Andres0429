from __future__ import annotations

from app.models import FieldResult, FieldsConfig, RawFindingsBundle, StructuredRecord


class StructuringAgent:
    def structure(self, raw: RawFindingsBundle, fields_cfg: FieldsConfig, config_hash: str) -> StructuredRecord:
        field_results: dict[str, FieldResult] = {}
        warnings = list(raw.warnings)

        grouped: dict[str, list] = {}
        for finding in raw.findings:
            grouped.setdefault(finding.field_name, []).append(finding)

        for field in fields_cfg.fields:
            candidates = grouped.get(field.name, [])
            if not candidates:
                field_results[field.name] = FieldResult(value=field.default, status="UNKNOWN", source=None)
                if field.required:
                    warnings.append(f"MISSING_REQUIRED:{field.name}")
                continue

            chosen = sorted(candidates, key=lambda item: item.confidence, reverse=True)[0]
            field_results[field.name] = FieldResult(
                value=chosen.raw_value,
                status="OK",
                source=chosen.source,
                evidence_refs=[chosen.evidence_id] if chosen.evidence_id else [],
            )

        return StructuredRecord(
            property_id=raw.property_id,
            fields=field_results,
            warnings=warnings,
            config_hash=config_hash,
        )
