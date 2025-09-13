from src.ingestion.lol_normalizers import normalize_match


def test_normalize_match_handles_missing_opponents():
    m = {"id": 1, "status": "not_started", "opponents": []}
    out = normalize_match(m)
    assert out["id"] == 1
    assert out["opponent1"] is None
