from app.pipeline import compute_target_build_sqft


def test_target_cap_1600():
    assert compute_target_build_sqft(2200, 1600) == 1600


def test_target_cap_with_missing_max_buildable_uses_cap():
    assert compute_target_build_sqft(None, 1600) == 1600
