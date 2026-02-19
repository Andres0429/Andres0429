import csv
import json

from app.pipeline import run_pipeline


def _write_input(path, property_id, address):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["property_id", "address_line1", "city", "state", "zip", "county"])
        writer.writeheader()
        writer.writerow(
            {
                "property_id": property_id,
                "address_line1": address,
                "city": "Nashville",
                "state": "TN",
                "zip": "37201",
                "county": "Davidson",
            }
        )


def test_pipeline_stub_warning_and_unknown(tmp_path):
    input_csv = tmp_path / "in.csv"
    output_csv = tmp_path / "out.csv"
    cache_db = tmp_path / "cache.sqlite"

    _write_input(input_csv, "P-REAL", "101 Real St")

    run_pipeline(
        input_csv=str(input_csv),
        output_csv=str(output_csv),
        fields_config="config/fields.yaml",
        calc_config="config/calculations.yaml",
        sources_config="config/sources.yaml",
        cache_db=str(cache_db),
        use_cache=False,
    )

    with open(output_csv, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows[0]["property_id"] == "P-REAL"
    warnings = json.loads(rows[0]["warnings"])
    assert "BROWSING_AGENT_STUB_NO_LIVE_EXTRACTION" in warnings
    assert rows[0]["lot_size_sqft"] == "UNKNOWN"


def test_pipeline_uses_cache_key_by_property(tmp_path):
    input_csv = tmp_path / "in.csv"
    output_csv1 = tmp_path / "out1.csv"
    output_csv2 = tmp_path / "out2.csv"
    cache_db = tmp_path / "cache.sqlite"

    _write_input(input_csv, "P1", "123 Main St")
    run_pipeline(
        input_csv=str(input_csv),
        output_csv=str(output_csv1),
        fields_config="config/fields.yaml",
        calc_config="config/calculations.yaml",
        sources_config="config/sources.yaml",
        cache_db=str(cache_db),
        use_cache=True,
    )

    _write_input(input_csv, "P2", "999 Different Ave")
    run_pipeline(
        input_csv=str(input_csv),
        output_csv=str(output_csv2),
        fields_config="config/fields.yaml",
        calc_config="config/calculations.yaml",
        sources_config="config/sources.yaml",
        cache_db=str(cache_db),
        use_cache=True,
    )

    with open(output_csv2, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert rows[0]["property_id"] == "P2"
