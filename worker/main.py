import redis
from common.models import LogEvent, MetricEvent
from worker.db import insert_logs_batch, insert_metrics_batch
from common.config import settings

r = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)

def ensure_group(stream: str, group: str):
    try:
        r.xgroup_create(stream, group, id="0", mkstream=True)
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise
def run_worker():
    ensure_group("logs_stream", "workers")
    ensure_group("metrics_stream", "workers")
    consumer_name = "worker-1"

    while True:
        entries = r.xreadgroup(
            groupname="workers",
            consumername=consumer_name,
            streams={"logs_stream": ">", "metrics_stream": ">"},
            count=100,
            block=500,
        )
        if not entries:
            continue

        for stream_name, messages in entries:
            if stream_name == "logs_stream":
                events = [LogEvent.model_validate_json(msg["data"]) for _, msg in messages]
                insert_logs_batch(events)
                r.xack("logs_stream", "workers", *[msg_id for msg_id, _ in messages])
            elif stream_name == "metrics_stream":
                events = [MetricEvent.model_validate_json(msg["data"]) for _, msg in messages]
                insert_metrics_batch(events)
                r.xack("metrics_stream", "workers", *[msg_id for msg_id, _ in messages])

if __name__ == '__main__':
    run_worker()