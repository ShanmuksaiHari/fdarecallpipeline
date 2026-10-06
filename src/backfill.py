"""
One-time historical load: fetch each year of FDA food recalls and land one
file per year in S3 (bronze). openFDA's food data starts in 2012, so earlier
years return no records.
"""
from fetch import fetch_window
from upload import upload_to_bronze

START_YEAR = 2004
END_YEAR = 2026


def main():
    for year in range(START_YEAR, END_YEAR + 1):
        records, meta = fetch_window(f"{year}0101", f"{year}1231")

        if records:
            upload_to_bronze(records, meta, key_label=f"{year}_full")


if __name__ == "__main__":
    main()
