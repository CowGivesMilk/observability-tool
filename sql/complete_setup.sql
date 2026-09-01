CREATE TABLE logs (
    time        TIMESTAMPTZ NOT NULL,
    service     TEXT NOT NULL,
    level       TEXT NOT NULL,
    message     TEXT NOT NULL,
    metadata    JSONB
);

SELECT create_hypertable('logs', 'time');

CREATE TABLE metrics (
    time        TIMESTAMPTZ NOT NULL,
    service     TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value       DOUBLE PRECISION NOT NULL,
    tags        JSONB
);

SELECT create_hypertable('metrics', 'time');

CREATE INDEX idx_logs_service_time ON logs (service, time DESC);
CREATE INDEX idx_metrics_service_metric_time ON metrics (service, metric_name, time DESC);

ALTER TABLE logs ADD COLUMN event_id UUID NOT NULL DEFAULT gen_random_uuid();
CREATE UNIQUE INDEX idx_logs_event_id ON logs (event_id, time);

ALTER TABLE metrics ADD COLUMN event_id UUID NOT NULL DEFAULT gen_random_uuid();
CREATE UNIQUE INDEX idx_metrics_event_id ON metrics (event_id, time);