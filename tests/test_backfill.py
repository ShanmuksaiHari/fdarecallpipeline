import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import backfill


def test_year_already_loaded_matches_only_that_year():
    keys = ["bronze/food/2026/09/22/recalls_2024_full.json"]
    assert backfill.year_already_loaded(2024, keys)
    assert not backfill.year_already_loaded(2025, keys)


def test_daily_files_do_not_count_as_a_loaded_year():
    keys = ["bronze/food/2026/10/06/recalls_daily_20260922_20261005.json"]
    assert not backfill.year_already_loaded(2026, keys)


def _setup(monkeypatch, existing):
    fetched, uploaded = [], []
    monkeypatch.setattr(backfill, "START_YEAR", 2024)
    monkeypatch.setattr(backfill, "END_YEAR", 2025)
    monkeypatch.setattr(backfill, "list_bronze_keys", lambda: existing)

    def fake_fetch(start, end):
        fetched.append(start[:4])
        return [{"recall_number": "H-1"}], {"meta": 1}

    monkeypatch.setattr(backfill, "fetch_window", fake_fetch)
    monkeypatch.setattr(
        backfill, "upload_to_bronze", lambda r, m, key_label: uploaded.append(key_label)
    )
    return fetched, uploaded


def test_resumes_by_skipping_loaded_years(monkeypatch):
    fetched, uploaded = _setup(
        monkeypatch, ["bronze/food/2026/09/22/recalls_2024_full.json"]
    )
    backfill.main([])
    assert fetched == ["2025"]
    assert uploaded == ["2025_full"]


def test_force_refetches_everything(monkeypatch):
    fetched, uploaded = _setup(
        monkeypatch, ["bronze/food/2026/09/22/recalls_2024_full.json"]
    )
    backfill.main(["--force"])
    assert fetched == ["2024", "2025"]
