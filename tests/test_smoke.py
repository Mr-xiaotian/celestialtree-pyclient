import os
import pytest

from celestialtree import Client


def _get_base_url() -> str | None:
    host = os.getenv("CTREE_HOST")
    port = os.getenv("CTREE_PORT")

    if not host or not port:
        return None

    return host, port


pytestmark = pytest.mark.skipif(
    _get_base_url() is None,
    reason="Smoke tests require CTREE_HOST and CTREE_PORT in environment or .env",
)


def test_health_smoke():
    host, port = _get_base_url()
    ct = Client(host, port)
    assert ct.health() is not None
