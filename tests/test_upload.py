import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import upload


class FakeS3:
    def __init__(self):
        self.calls = []

    def put_object(self, **kwargs):
        self.calls.append(kwargs)


def test_upload_writes_expected_key_and_body(monkeypatch):
    fake = FakeS3()
    monkeypatch.setattr(upload, "s3", fake)
    monkeypatch.setattr(upload, "BUCKET_NAME", "test-bucket")

    records = [{"recall_number": "H-1"}]
    key = upload.upload_to_bronze(records, {"last_updated": "x"}, key_label="daily_20260930")

    assert key.startswith("bronze/food/")
    assert key.endswith("/recalls_daily_20260930.json")

    call = fake.calls[0]
    assert call["Bucket"] == "test-bucket"
    assert call["Key"] == key
    body = json.loads(call["Body"])
    assert body["results"] == records
    assert body["meta"] == {"last_updated": "x"}


def test_upload_without_bucket_fails_with_clear_error(monkeypatch):
    monkeypatch.setattr(upload, "s3", FakeS3())
    monkeypatch.setattr(upload, "BUCKET_NAME", None)

    with pytest.raises(RuntimeError, match="AWS_BUCKET_NAME"):
        upload.upload_to_bronze([], {})
