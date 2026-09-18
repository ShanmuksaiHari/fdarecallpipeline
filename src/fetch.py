import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.fda.gov/food/enforcement.json"
API_KEY = os.getenv("FDA_API_KEY")
PAGE_SIZE = 1000  # max allowed by the API
SKIP_LIMIT = 25000  # openFDA stops paging around 26k, so we stay under it


def fetch_window(start_date, end_date):
    """
    Get all food recall records with report_date in [start_date, end_date].
    Dates should be strings like "20260101".
    Returns a list of records, plus the meta block from the first response.
    """
    search = f"report_date:[{start_date} TO {end_date}]"
    params = {
        "api_key": API_KEY,
        "search": search,
        "limit": PAGE_SIZE,
        "skip": 0,
    }

    response = requests.get(BASE_URL, params=params)

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
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        records.extend(response.json()["results"])
        time.sleep(0.3)  # be polite, stay well under the rate limit

    print(f"{start_date} to {end_date}: got {len(records)} of {total} records")

    if len(records) != total:
        print("WARNING: record count doesn't match what the API reported")

    return records, meta


if __name__ == "__main__":
    records, meta = fetch_window("20260801", "20260909")

    if records:
        print(f"\nFeed last updated: {meta['last_updated']}")
        print(f"\nFirst record fields:")
        for key, value in records[0].items():
            print(f"  {key}: {value}")
