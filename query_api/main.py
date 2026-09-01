from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from query_api.db import query_logs, query_metrics


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


class LogsQuery(BaseModel):
    service: str | None = None
    level: str | None = None
    since_minutes: int = 60
    limit: int = 100


@app.get("/logs")
def get_logs(query: LogsQuery = Depends()):
    since = datetime.now(timezone.utc) - timedelta(minutes=query.since_minutes)

    return query_logs(
        query.service,
        query.level,
        since,
        query.limit,
    )


class MetricQuery(BaseModel):
    service: str | None = None
    metric_name: str | None = None
    since_minutes: int = 60
    bucket_minutes: int = 1


@app.get("/metrics")
def get_metrics(query: MetricQuery = Depends()):
    since = datetime.now(timezone.utc) - timedelta(minutes=query.since_minutes)
    bucket_width = timedelta(minutes=query.bucket_minutes)

    return query_metrics(
        query.service,
        query.metric_name,
        since,
        bucket_width,
    )