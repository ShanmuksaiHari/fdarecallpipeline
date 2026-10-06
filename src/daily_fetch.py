"""
Daily job: fetch recent FDA food recalls and land them in S3 (bronze).

The FDA publishes recalls in weekly batches, and openFDA can load a batch a
day or more after its report date. Fetching only "yesterday" could miss a
batch, so by default this re-fetches the last LOOKBACK_DAYS days every run.
That is safe to repeat: silver de-duplicates by recall_number (newest file wins).

Usage:
    python daily_fetch.py              # last 14 days, ending yesterday (UTC)
    python daily_fetch.py 20260923     # one specific report date, e.g. to test
"""
import sys
from datetime import datetime, timedelta, timezone

from fetch import fetch_window
from upload import upload_to_bronze

LOOKBACK_DAYS = 14


def get_window(argv, now=None):
    """Return (start, end) as YYYYMMDD strings for the dates to fetch."""
    if len(argv) > 1 and argv[1]:
        datetime.strptime(argv[1], "%Y%m%d")  # fail early on a bad format
        return argv[1], argv[1]

    now = now or datetime.now(timezone.utc)
    end = now - timedelta(days=1)
    start = now - timedelta(days=LOOKBACK_DAYS)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def main(argv):
    start, end = get_window(argv)

    records, meta = fetch_window(start, end)
    print(f"{start} to {end}: got {len(records)} records")

    if records:
        # the dates in the label keep files from different runs from
        # overwriting each other
        upload_to_bronze(records, meta, key_label=f"daily_{start}_{end}")
    else:
        print("No recalls in this window, skipping upload.")


if __name__ == "__main__":
    main(sys.argv)
