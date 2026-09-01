from fastapi import FastAPI, HTTPException
from common.models import LogEvent, MetricEvent
from common.redis_client import publish_log, publish_metric
ACCEPTED = 202
SERVICE_UNAVAILABLE = 503

app = FastAPI()

@app.post("/logs", status_code=ACCEPTED)
def ingest_log(event: LogEvent):
    try:
        publish_log(event)
    except Exception as e:
        raise HTTPException(status_code=SERVICE_UNAVAILABLE, detail=f"Failed to queue log: {e}")
    return {"event_id": str(event.event_id)}



@app.post("/metrics", status_code=ACCEPTED)
def ingest_metric(event: MetricEvent):
    try:
        publish_metric(event)
    except Exception as e:
        raise HTTPException(status_code=SERVICE_UNAVAILABLE, detail=f"Failed to queue metric: {e}")
    return {"event_id": str(event.event_id)}
