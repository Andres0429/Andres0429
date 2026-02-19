from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass
class ExtractionHints:
    keywords: list[str] = field(default_factory=list)
    selectors: list[str] = field(default_factory=list)
    evidence_required: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ExtractionHints":
        data = data or {}
        return cls(
            keywords=list(data.get("keywords", [])),
            selectors=list(data.get("selectors", [])),
            evidence_required=bool(data.get("evidence_required", True)),
        )


@dataclass
class ValidatorSpec:
    min: float | None = None
    max: float | None = None
    regex: str | None = None
    unit: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ValidatorSpec":
        data = data or {}
        min_value = data.get("min")
        max_value = data.get("max")
        if min_value is not None and max_value is not None and float(max_value) < float(min_value):
            raise ValueError("validators.max must be >= validators.min")
        return cls(min=min_value, max=max_value, regex=data.get("regex"), unit=data.get("unit"))


@dataclass
class FieldSpec:
    name: str
    output_column: str
    dtype: Literal["str", "int", "float", "bool"]
    required: bool = True
    default: Any = "UNKNOWN"
    extraction_hints: ExtractionHints = field(default_factory=ExtractionHints)
    preferred_sources: list[str] = field(default_factory=list)
    validators: ValidatorSpec = field(default_factory=ValidatorSpec)
    dependencies: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FieldSpec":
        dtype = data["dtype"]
        if dtype not in {"str", "int", "float", "bool"}:
            raise ValueError(f"invalid dtype '{dtype}'")
        return cls(
            name=data["name"],
            output_column=data["output_column"],
            dtype=dtype,
            required=bool(data.get("required", True)),
            default=data.get("default", "UNKNOWN"),
            extraction_hints=ExtractionHints.from_dict(data.get("extraction_hints")),
            preferred_sources=list(data.get("preferred_sources", [])),
            validators=ValidatorSpec.from_dict(data.get("validators")),
            dependencies=list(data.get("dependencies", [])),
        )


@dataclass
class FieldsConfig:
    fields: list[FieldSpec]

    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> "FieldsConfig":
        return cls(fields=[FieldSpec.from_dict(item) for item in data.get("fields", [])])


@dataclass
class ARVSpec:
    strategy: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class MAOSpec:
    strategy: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class CalculationsConfig:
    target_cap_sqft: int
    arv: ARVSpec
    mao: MAOSpec

    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> "CalculationsConfig":
        return cls(
            target_cap_sqft=int(data.get("target_cap_sqft", 1600)),
            arv=ARVSpec(**data["arv"]),
            mao=MAOSpec(**data["mao"]),
        )


@dataclass
class SourcesConfig:
    default: dict[str, list[str]] = field(default_factory=dict)
    jurisdiction_overrides: dict[str, dict[str, dict[str, list[str]]]] = field(default_factory=dict)

    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> "SourcesConfig":
        return cls(
            default=data.get("default", {}),
            jurisdiction_overrides=data.get("jurisdiction_overrides", {}),
        )


@dataclass
class Evidence:
    evidence_id: str
    url: str
    timestamp_utc: datetime
    snippet: str | None = None
    notes: str | None = None


@dataclass
class RawFinding:
    field_name: str
    raw_value: Any
    source: str
    confidence: float = 0.5
    evidence_id: str | None = None
    notes: str | None = None


@dataclass
class RawFindingsBundle:
    property_id: str
    address: str
    session_id: str
    findings: list[RawFinding] = field(default_factory=list)
    evidence: list[Evidence | dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class FieldResult:
    value: Any
    status: Literal["OK", "UNKNOWN", "INVALID"]
    source: str | None = None
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class StructuredRecord:
    property_id: str
    fields: dict[str, FieldResult]
    warnings: list[str] = field(default_factory=list)
    config_hash: str = ""


@dataclass
class CalcResult:
    value: float | None
    warnings: list[str] = field(default_factory=list)


@dataclass
class PropertyInput:
    property_id: str
    address_line1: str
    city: str
    state: str = "TN"
    zip: str | None = None
    county: str | None = None

    @classmethod
    def model_validate(cls, data: dict[str, Any]) -> "PropertyInput":
        property_id = str(data["property_id"]).strip()
        if not property_id:
            raise ValueError("property_id cannot be empty")
        return cls(
            property_id=property_id,
            address_line1=data["address_line1"],
            city=data["city"],
            state=data.get("state", "TN"),
            zip=data.get("zip"),
            county=data.get("county"),
        )
