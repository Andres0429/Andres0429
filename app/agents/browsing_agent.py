from __future__ import annotations

from app.models import PropertyInput, RawFindingsBundle


class BrowsingAgent:
    """MVP placeholder browser.

    This scaffold does not perform live browsing yet. It returns no findings and
    explicitly records a warning so downstream output is deterministic and honest.
    """

    def run_property_session(self, prop: PropertyInput, source_plan: dict[str, list[str]]) -> RawFindingsBundle:
        session_id = f"sess_{prop.property_id}"

        return RawFindingsBundle(
            property_id=prop.property_id,
            address=f"{prop.address_line1}, {prop.city}, {prop.state}",
            session_id=session_id,
            findings=[],
            evidence=[],
            warnings=["BROWSING_AGENT_STUB_NO_LIVE_EXTRACTION"],
        )
