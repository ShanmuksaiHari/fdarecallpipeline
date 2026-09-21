import os
import json
from datetime import datetime, timezone

import boto3
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

s3 = boto3.client("s3")


def upload_to_bronze(records, meta):
    now = datetime.now(timezone.utc)
    key = now.strftime("bronze/food/%Y/%m/%d/recalls_%H%M.json")

    body = {
        "meta": meta,
        "results": records,
    }

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(body),
        ContentType="application/json",
    )

    print(f"Uploaded {len(records)} records to s3://{BUCKET_NAME}/{key}")
    return key
