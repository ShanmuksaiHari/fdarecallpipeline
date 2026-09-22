from fetch import fetch_window
from upload import upload_to_bronze

START_YEAR = 2004
END_YEAR = 2026

for year in range(START_YEAR, END_YEAR + 1):
    start_date = f"{year}0101"
    end_date = f"{year}1231"

    records, meta = fetch_window(start_date, end_date)

    if records:
        upload_to_bronze(records, meta, key_label=f"{year}_full")
