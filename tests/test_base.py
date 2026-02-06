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
    reason="Tests require CTREE_HOST and CTREE_PORT in environment or .env",
)


def test_payload_roundtrip_http():
    host, port = _get_base_url()
    client = Client(host, port)

    payload = {
        "type": "bench",
        "parents": [],
        "message": "bench payload 1B",
        "payload": 0,
    }
    event_id = client.emit("test", payload=payload)
    event = client.get_event(event_id)

    assert event["payload"] == payload


def test_payload_roundtrip_grpc():
    host, port = _get_base_url()
    client = Client(host, port)

    payload = {
        "type": "bench",
        "parents": [],
        "message": "bench payload 1B",
        "payload": 0,
    }
    event_id = client.emit_grpc("test", payload=payload)
    event = client.get_event(event_id)

    assert event["payload"] == payload