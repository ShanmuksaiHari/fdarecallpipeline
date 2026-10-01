from datetime import datetime, timedelta, timezone
from fetch import fetch_window
from upload import upload_to_bronze

yesterday = datetime.now(timezone.utc) - timedelta(days=1)
date_str = yesterday.strftime("%Y%m%d")

records, meta = fetch_window(date_str, date_str)
print(f"{date_str}: got {len(records)} records")

if records:
    upload_to_bronze(records, meta, key_label="daily")
else:
    print("No new recalls for this date, skipping upload.")
