# worker/db.py
import psycopg
from common.models import LogEvent, MetricEvent
from common.config import settings

DB_URL = settings.db_url

def insert_logs_batch(events: list[LogEvent]) -> None:
    if not events:
        return

    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO logs (event_id, time, service, level, message, metadata)
                VALUES (%(event_id)s, %(time)s, %(service)s, %(level)s, %(message)s, %(metadata)s)
                ON CONFLICT (event_id, time) DO NOTHING
                """,
                [
                    {
                        "event_id": str(e.event_id),
                        "time": e.time,
                        "service": e.service,
                        "level": e.level,
                        "message": e.message,
                        "metadata": psycopg.types.json.Json(e.metadata) if e.metadata else None,
                    }
                    for e in events
                ],
            )
        conn.commit()
def insert_metrics_batch(events: list[MetricEvent]) -> None:
    if not events:
        return
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO metrics (event_id, time, service, metric_name, value, tags)
                VALUES (%(event_id)s, %(time)s, %(service)s, %(metric_name)s, %(value)s, %(tags)s)
                ON CONFLICT (event_id, time) DO NOTHING
                """,
                [
                    {
                        "event_id": str(e.event_id),
                        "time": e.time,
                        "service": e.service,
                        "metric_name": e.metric_name,
                        "value": e.value,
                        "tags": psycopg.types.json.Json(e.tags) if e.tags else None,
                    }
                    for e in events
                ],
            )
        conn.commit()