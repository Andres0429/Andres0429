import pytest

from app.registry import Registry


def test_registry_register_and_get():
    r = Registry()

    @r.register("arv", "x")
    def _x(**kwargs):
        return 1

    assert r.get("arv", "x")() == 1


def test_registry_missing_name_raises_clear_error():
    r = Registry()
    with pytest.raises(ValueError, match="not registered"):
        r.get("arv", "missing")
