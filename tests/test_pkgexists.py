import pytest


def test_package_exists():
    import jott as pkg
    assert pkg is not None
