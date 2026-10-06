"""
Historical load: fetch each year of FDA food recalls and land one file per
year in S3 (bronze). openFDA's food data starts in 2012, so earlier years
return no records.

The load can be resumed: years that already have a file in S3 are skipped, so
a failure partway through no longer means starting again from the beginning.

Usage:
    python backfill.py            # skip years already in S3
    python backfill.py --force    # re-fetch every year
"""
import sys

from fetch import fetch_window
from upload import list_bronze_keys, upload_to_bronze

START_YEAR = 2004
END_YEAR = 2026


def year_already_loaded(year, existing_keys):
    suffix = f"/recalls_{year}_full.json"
    return any(key.endswith(suffix) for key in existing_keys)


def main(argv=None):
    force = "--force" in (argv or [])
    existing_keys = [] if force else list_bronze_keys()

    for year in range(START_YEAR, END_YEAR + 1):
        if year_already_loaded(year, existing_keys):
            print(f"{year}: already in S3, skipping")
            continue

        records, meta = fetch_window(f"{year}0101", f"{year}1231")

        # years with no records (before 2012) write no file, so they are
        # simply re-checked on the next run - one cheap request each
        if records:
            upload_to_bronze(records, meta, key_label=f"{year}_full")


if __name__ == "__main__":
    main(sys.argv[1:])
