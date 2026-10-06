# Databricks notebook source
import boto3

# Credentials are never committed. Create a Databricks secret scope named
# 'fda-pipeline' holding the two AWS keys below before running this notebook.
s3 = boto3.client(
    "s3",
    aws_access_key_id=dbutils.secrets.get(scope="fda-pipeline", key="aws_access_key_id"),
    aws_secret_access_key=dbutils.secrets.get(scope="fda-pipeline", key="aws_secret_access_key"),
)

response = s3.list_objects_v2(Bucket="fda-recalls-shanmuksai", Prefix="bronze/")
for obj in response.get("Contents", []):
    print(obj["Key"])

# COMMAND ----------

import json
from pyspark.sql.types import StructType, StructField, StringType
from pyspark.sql.functions import to_date, col, udf
from pyspark.sql.types import StringType as PySparkStringType


def categorize_hazard(reason_text):
    if reason_text is None:
        return "other"
    text = reason_text.lower()
    if "undeclared" in text or "does not declare" in text or "do not declare" in text or "not declared" in text or "does not list" in text:
        return "allergen"
    pathogens = ["salmonella", "listeria", "botulinum", "e. coli", "cyclospora", "patulin", "giardia", "norovirus"]
    if any(p in text for p in pathogens):
        return "pathogen"
    if "foreign object" in text or "foreign material" in text or "metal" in text or "plastic" in text or "glass" in text:
        return "foreign_material"
    return "other"


recall_schema = StructType([
    StructField("recall_number", StringType(), False),
    StructField("status", StringType(), True),
    StructField("state", StringType(), True),
    StructField("classification", StringType(), True),
    StructField("recalling_firm", StringType(), True),
    StructField("product_description", StringType(), True),
    StructField("reason_for_recall", StringType(), True),
    StructField("recall_initiation_date", StringType(), True),
    StructField("report_date", StringType(), True),
    StructField("center_classification_date", StringType(), True),
    StructField("termination_date", StringType(), True),
])

# Read every bronze file (backfill AND daily), not a fixed list of paths.
# Files are processed oldest-first, so if a recall shows up in more than one
# file (e.g. a status update), the newest version wins. Keying by
# recall_number also guarantees one row per recall, which the MERGE needs.
paginator = s3.get_paginator("list_objects_v2")
keys = []
for page in paginator.paginate(Bucket="fda-recalls-shanmuksai", Prefix="bronze/food/"):
    for obj in page.get("Contents", []):
        if obj["Key"].endswith(".json"):
            keys.append(obj["Key"])
keys.sort()

records_by_number = {}
for key in keys:
    body = json.loads(s3.get_object(Bucket="fda-recalls-shanmuksai", Key=key)["Body"].read())
    for r in body["results"]:
        records_by_number[r["recall_number"]] = r
    print(f"{key}: {len(body['results'])} records")

all_records = list(records_by_number.values())
print(f"\nTotal unique recalls: {len(all_records)}")

df_all = spark.createDataFrame(all_records, schema=recall_schema)

for date_col in ["recall_initiation_date", "report_date", "center_classification_date", "termination_date"]:
    df_all = df_all.withColumn(date_col, to_date(col(date_col), "yyyyMMdd"))

categorize_udf = udf(categorize_hazard, PySparkStringType())
df_all = df_all.withColumn("hazard_category", categorize_udf(col("reason_for_recall")))

print(f"\nFinal row count: {df_all.count()}")
df_all.groupBy("hazard_category").count().show()

# COMMAND ----------

from delta.tables import DeltaTable

if spark.catalog.tableExists("silver_recalls"):
    silver_table = DeltaTable.forName(spark, "silver_recalls")

    (silver_table.alias("target")
        .merge(
            df_all.alias("source"),
            "target.recall_number = source.recall_number"
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute())

    print("Merge complete")
else:
    df_all.write.format("delta").saveAsTable("silver_recalls")
    print("Table created fresh")

spark.sql("SELECT COUNT(*) as total_rows FROM silver_recalls").show()

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE TABLE recalls_by_year_class AS
SELECT
    YEAR(report_date) AS year,
    classification,
    COUNT(*) AS recall_count
FROM silver_recalls
WHERE report_date IS NOT NULL
GROUP BY YEAR(report_date), classification
ORDER BY year, classification
""")

spark.sql("SELECT * FROM recalls_by_year_class ORDER BY year DESC LIMIT 10").show()

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE TABLE recalls_by_state AS
SELECT
    state,
    COUNT(*) AS recall_count
FROM silver_recalls
WHERE state IS NOT NULL
GROUP BY state
ORDER BY recall_count DESC
""")

spark.sql("SELECT * FROM recalls_by_state LIMIT 10").show()


# COMMAND ----------

spark.sql("""
CREATE OR REPLACE TABLE recalls_by_firm AS
SELECT
    recalling_firm,
    COUNT(*) AS recall_count
FROM silver_recalls
WHERE recalling_firm IS NOT NULL
GROUP BY recalling_firm
ORDER BY recall_count DESC
LIMIT 20
""")

spark.sql("SELECT * FROM recalls_by_firm LIMIT 10").show()

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE TABLE recalls_by_hazard AS
SELECT
    YEAR(report_date) AS year,
    hazard_category,
    COUNT(*) AS recall_count
FROM silver_recalls
WHERE report_date IS NOT NULL
GROUP BY YEAR(report_date), hazard_category
ORDER BY year, hazard_category
""")

spark.sql("SELECT * FROM recalls_by_hazard ORDER BY year DESC LIMIT 10").show()

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE TABLE disclosure_lag AS
SELECT
    recall_number,
    recalling_firm,
    classification,
    recall_initiation_date,
    report_date,
    DATEDIFF(report_date, recall_initiation_date) AS lag_days
FROM silver_recalls
WHERE recall_initiation_date IS NOT NULL
  AND report_date IS NOT NULL
  AND recall_initiation_date >= '2004-01-01'
  AND recall_initiation_date <= CURRENT_DATE()
""")

spark.sql("""
SELECT
    MIN(lag_days) AS min_lag,
    AVG(lag_days) AS avg_lag,
    MAX(lag_days) AS max_lag,
    COUNT(*) AS total_rows
FROM disclosure_lag
""").show()

# COMMAND ----------

spark.sql("""
CREATE OR REPLACE TABLE latest_class_one AS
SELECT
    recall_number,
    recalling_firm,
    state,
    product_description,
    reason_for_recall,
    hazard_category,
    report_date,
    status
FROM silver_recalls
WHERE classification = 'Class I'
ORDER BY report_date DESC
LIMIT 25
""")

spark.sql("SELECT recall_number, recalling_firm, state, report_date, status FROM latest_class_one LIMIT 10").show()
