import os
import sys
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import daily_fetch


NOW = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)


def test_default_window_ends_yesterday_and_looks_back():
    start, end = daily_fetch.get_window(["daily_fetch.py"], now=NOW)
    assert end == "20261007"  # yesterday
    assert start == "20260924"  # 14 days back


def test_empty_argument_uses_default_window():
    # GitHub Actions passes "" when no report_date is entered
    start, end = daily_fetch.get_window(["daily_fetch.py", ""], now=NOW)
    assert end == "20261007"


def test_specific_date_argument_is_a_single_day():
    assert daily_fetch.get_window(["daily_fetch.py", "20260923"]) == ("20260923", "20260923")


def test_bad_date_argument_fails_early():
    with pytest.raises(ValueError):
        daily_fetch.get_window(["daily_fetch.py", "2026-09-23"])
