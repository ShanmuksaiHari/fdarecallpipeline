from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    "owner": "shanmuksai",
    "retries": 1,
}

with DAG(
    dag_id="fda_recall_pipeline",
    description="Fetch daily FDA recalls and trigger Databricks silver/gold rebuild",
    default_args=default_args,
    schedule_interval="0 12 * * *",
    start_date=datetime(2026, 10, 1),
    catchup=False,
    tags=["fda", "portfolio"],
) as dag:

    fetch_task = BashOperator(
        task_id="fetch_daily_recalls",
        bash_command="cd /opt/airflow/project/src && python daily_fetch.py",
    )

    trigger_databricks_task = BashOperator(
        task_id="trigger_databricks_job",
        bash_command=(
            'curl -X POST "$DATABRICKS_HOST/api/2.1/jobs/run-now" '
            '-H "Authorization: Bearer $DATABRICKS_TOKEN" '
            '-H "Content-Type: application/json" '
            '-d "{\\"job_id\\": $DATABRICKS_JOB_ID}"'
        ),
    )

    fetch_task >> trigger_databricks_task
