# common/redis_client.py

import redis

from .models import LogEvent, MetricEvent


from common.config import settings

r = redis.Redis(
    host=settings.redis_host, 
    port=settings.redis_port, 
    decode_responses=True)


def publish_log(event: LogEvent):
    r.xadd("logs_stream", {"data": event.model_dump_json()})


def publish_metric(event: MetricEvent):
    r.xadd("metrics_stream", {"data": event.model_dump_json()})