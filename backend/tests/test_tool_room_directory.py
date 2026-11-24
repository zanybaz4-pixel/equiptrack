"""Check the owner-reviewed transcription before any database import."""
import json
from pathlib import Path
import re


def test_reviewed_directory_has_174_valid_unique_entries():
    items = json.loads((Path(__file__).parents[1] / "migrations/data/tool_room_directory_2026.json").read_text(encoding="utf-8"))["items"]
    assert len(items) == len({item["key"] for item in items}) == 174
    assert len({item["name"].casefold() for item in items}) == 174
    for item in items:
        assert 0 < len(item["name"]) <= 120
        racks = item["storage_rack"].split(", ")
        assert all(re.fullmatch(r"MT\d{2}", rack) for rack in racks)
        if item["location"] not in ("N/A", "Not recorded"):
            codes = item["location"].split(", ")
            assert len(codes) == len(racks)
            assert all(code.startswith(rack + ".") and re.fullmatch(r"MT\d{2}\.\d{2}", code)
                       for rack, code in zip(racks, codes))
    assert next(item for item in items if item["name"] == "Welding apron")["location"] == "Not recorded"
    assert next(item for item in items if "handwritten entry" in item["name"])["notes"]
