import os
import sys

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import fetch


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code} error")


def make_payload(total, n_records):
    return {
        "meta": {"results": {"total": total}, "last_updated": "2026-01-01"},
        "results": [{"recall_number": f"H-{i}"} for i in range(n_records)],
    }


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    # keep retry/backoff and polite-delay sleeps from slowing the tests down
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)


def test_404_means_no_records(monkeypatch):
    monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: FakeResponse(404))
    records, meta = fetch.fetch_window("20260101", "20260101")
    assert records == []
    assert meta is None


def test_single_page(monkeypatch):
    monkeypatch.setattr(
        fetch.requests, "get", lambda *a, **k: FakeResponse(200, make_payload(3, 3))
    )
    records, meta = fetch.fetch_window("20260101", "20260131")
    assert len(records) == 3
    assert meta["last_updated"] == "2026-01-01"


def test_pages_until_total_reached(monkeypatch):
    responses = iter([
        FakeResponse(200, make_payload(total=3, n_records=2)),
        FakeResponse(200, make_payload(total=3, n_records=1)),
    ])
    monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: next(responses))
    records, _ = fetch.fetch_window("20260101", "20260131")
    assert len(records) == 3


def test_retries_server_error_then_succeeds(monkeypatch):
    responses = iter([FakeResponse(503), FakeResponse(200, make_payload(1, 1))])
    monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: next(responses))
    records, _ = fetch.fetch_window("20260101", "20260101")
    assert len(records) == 1


def test_gives_up_after_max_retries(monkeypatch):
    monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: FakeResponse(500))
    with pytest.raises(requests.exceptions.HTTPError):
        fetch.fetch_window("20260101", "20260101")


def test_client_error_is_not_retried(monkeypatch):
    calls = []

    def fake_get(*a, **k):
        calls.append(1)
        return FakeResponse(400)

    monkeypatch.setattr(fetch.requests, "get", fake_get)
    with pytest.raises(requests.exceptions.HTTPError):
        fetch.fetch_window("20260101", "20260101")
    assert len(calls) == 1


def test_too_many_records_raises(monkeypatch):
    monkeypatch.setattr(
        fetch.requests,
        "get",
        lambda *a, **k: FakeResponse(200, make_payload(fetch.SKIP_LIMIT + 1, 1)),
    )
    with pytest.raises(ValueError):
        fetch.fetch_window("20040101", "20261231")


def test_api_key_only_sent_when_set(monkeypatch):
    seen = []

    def fake_get(url, params=None, **k):
        seen.append(dict(params))
        return FakeResponse(200, make_payload(1, 1))

    monkeypatch.setattr(fetch.requests, "get", fake_get)

    monkeypatch.setattr(fetch, "API_KEY", None)
    fetch.fetch_window("20260101", "20260101")
    assert "api_key" not in seen[-1]

    monkeypatch.setattr(fetch, "API_KEY", "abc123")
    fetch.fetch_window("20260101", "20260101")
    assert seen[-1]["api_key"] == "abc123"
