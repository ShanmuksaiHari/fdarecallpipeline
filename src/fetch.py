import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.fda.gov/food/enforcement.json"
API_KEY = os.getenv("FDA_API_KEY")
PAGE_SIZE = 1000  # max allowed by the API
SKIP_LIMIT = 25000  # openFDA stops paging around 26k, so we stay under it
MAX_RETRIES = 3


def _get_with_retry(params):
    """
    GET against the openFDA endpoint with basic retry/backoff for transient
    failures (network blips, 5xx). Does not retry 404 (no results) or other
    4xx errors - those are real responses, not transient failures.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(BASE_URL, params=params, timeout=30)
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"  request failed (attempt {attempt}/{MAX_RETRIES}): {e}")
            time.sleep(2 ** attempt)  # 2s, 4s, 8s
            continue

        if response.status_code == 404:
            return response  # not an error - just no matching records

        if response.status_code >= 500:
            last_error = requests.exceptions.HTTPError(
                f"{response.status_code} server error"
            )
            print(f"  server error (attempt {attempt}/{MAX_RETRIES}): "
                  f"{response.status_code}")
            time.sleep(2 ** attempt)
            continue

        return response  # success, or a 4xx we want to raise on immediately

    raise last_error


def fetch_window(start_date, end_date):
    """
    Get all food recall records with report_date in [start_date, end_date].
    Dates should be strings like "20260101".
    Returns a list of records, plus the meta block from the first response.
    """
    search = f"report_date:[{start_date} TO {end_date}]"
    params = {
        "search": search,
        "limit": PAGE_SIZE,
        "skip": 0,
    }
    if API_KEY:  # works without a key too, just with lower rate limits
        params["api_key"] = API_KEY

    response = _get_with_retry(params)

    # openFDA returns 404 when nothing matches the search, not an error
    if response.status_code == 404:
        print(f"{start_date} to {end_date}: no records found")
        return [], None

    response.raise_for_status()
    data = response.json()

    meta = data["meta"]
    total = meta["results"]["total"]
    records = data["results"]

    if total > SKIP_LIMIT:
        raise ValueError(
            f"{start_date}-{end_date} has {total} records, over the paging "
            f"limit of {SKIP_LIMIT}. Use a smaller date range."
        )

    # keep paging until we have everything the API says is there
    while len(records) < total:
        params["skip"] = len(records)
        response = _get_with_retry(params)
        response.raise_for_status()
        records.extend(response.json()["results"])
        time.sleep(0.3)  # be polite, stay well under the rate limit

    print(f"{start_date} to {end_date}: got {len(records)} of {total} records")

    if len(records) != total:
        print("WARNING: record count doesn't match what the API reported")

    return records, meta


if __name__ == "__main__":
    # Manual smoke test: fetch the last 7 days and print the first record's
    # fields, to sanity-check the API connection and response shape.
    from datetime import datetime, timedelta, timezone

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)

    records, meta = fetch_window(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))

    if records:
        print(f"\nFeed last updated: {meta['last_updated']}")
        print("\nFirst record fields:")
        for key, value in records[0].items():
            print(f"  {key}: {value}")
