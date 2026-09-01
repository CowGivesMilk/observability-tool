import psycopg
from datetime import datetime, timedelta, timezone
from common.config import settings
DB_URL = settings.db_url


def query_logs(service: str | None, level: str | None, since: datetime, limit: int) -> list[dict]:
    conditions = ["time > %(since)s"]
    params = {"since": since, "limit": limit}

    if service:
        conditions.append("service = %(service)s")
        params["service"] = service
    if level:
        conditions.append("level = %(level)s")
        params["level"] = level

    where_clause = " AND ".join(conditions)

    with psycopg.connect(DB_URL) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                f"""
                SELECT time, service, level, message, metadata, event_id
                FROM logs
                WHERE {where_clause}
                ORDER BY time DESC
                LIMIT %(limit)s
                """,
                params,
            )
            return cur.fetchall()

def query_metrics(service: str | None, metric_name: str | None, since: datetime, bucket_width: timedelta) -> list[dict]:
    conditions = ["time > %(since)s"]
    params = {"since": since, "bucket": bucket_width}
    if service:
        conditions.append("service = %(service)s")
        params["service"] = service
    if metric_name:
        conditions.append("metric_name = %(metric_name)s")
        params["metric_name"] = metric_name
    where_clause = " AND ".join(conditions)
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                f"""
                SELECT
                    time_bucket(%(bucket)s, time) AS bucket,
                    avg(value) AS avg_value,
                    max(value) AS max_value,
                    min(value) AS min_value
                FROM metrics
                WHERE {where_clause}
                GROUP BY bucket
                ORDER BY bucket;
                """,
                params,
            )
            return cur.fetchall()