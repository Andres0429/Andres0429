from __future__ import annotations

from datetime import datetime, timezone

from app.models import PropertyInput, RawFinding, RawFindingsBundle


class BrowsingAgent:
    """Placeholder browsing agent with deterministic mock extraction for MVP scaffolding.

    In production this class should first try Computer Use via Responses API,
    then fallback to Playwright headed mode.
    """

    def run_property_session(self, prop: PropertyInput, source_plan: dict[str, list[str]]) -> RawFindingsBundle:
        session_id = f"sess_{prop.property_id}"
        findings: list[RawFinding] = []
        warnings: list[str] = []

        # Deterministic stub data; real version should scrape sources in source_plan.
        findings.append(
            RawFinding(
                field_name="lot_size_sqft",
                raw_value=7405,
                source="official_county",
                confidence=0.9,
                evidence_id="ev1",
                notes="Stub parcel lot size",
            )
        )
        findings.append(
            RawFinding(
                field_name="zoning_code",
                raw_value="R6",
                source="city_zoning",
                confidence=0.8,
                evidence_id="ev2",
                notes="Stub zoning",
            )
        )

        return RawFindingsBundle(
            property_id=prop.property_id,
            address=f"{prop.address_line1}, {prop.city}, {prop.state}",
            session_id=session_id,
            findings=findings,
            evidence=[
                {
                    "evidence_id": "ev1",
                    "url": "https://example-county.test/property",
                    "timestamp_utc": datetime.now(timezone.utc),
                    "snippet": "Lot Size: 7,405 sqft",
                },
                {
                    "evidence_id": "ev2",
                    "url": "https://example-city-zoning.test/parcel",
                    "timestamp_utc": datetime.now(timezone.utc),
                    "snippet": "Zoning: R6",
                },
            ],
            warnings=warnings,
        )
