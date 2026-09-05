# Observability Tool

A self-built observability pipeline for collecting, buffering, storing, querying, and visualizing application **logs and metrics**.

The project implements the core pieces of a small observability platform from scratch using **FastAPI, Redis Streams, TimescaleDB, PostgreSQL, Next.js, React, and Recharts**.

It is designed as a hands-on systems/backend engineering project for understanding how telemetry moves from applications into a durable time-series store and finally into a live dashboard.
### **NOTE**
> 1. I do not have good knowledge of frontend and frontend was made with the help of AI. At least for a moment I am not intersted in frontend stuff only due to my development experience while working with frontend. I just wanted a project with a frontend.
> 2. This project is built and tested on Linux. It should work well with MacOS but I cann't guarantee it especially for windows.
---

## What it does

The system accepts structured telemetry from applications and processes it through a decoupled ingestion pipeline.

For each log or metric event, the system:

1. Receives the event through a FastAPI ingestion endpoint.
2. Validates it using shared Pydantic models.
3. Generates an event UUID and UTC timestamp when they are not supplied.
4. Publishes the event to a Redis Stream.
5. Lets a separate worker consume queued events.
6. Writes events to TimescaleDB in batches.
7. Acknowledges Redis messages only after database persistence.
8. Exposes stored telemetry through a separate query API.
9. Aggregates metric values into time buckets using TimescaleDB.
10. Displays recent logs, latency, and error-rate metrics in a Next.js dashboard.
11. Includes a traffic generator that simulates healthy services and temporary incidents.

This keeps telemetry ingestion separate from database persistence and visualization.

---

# Architecture

```mermaid
flowchart TD
    A[Applications <br>Traffic Generator] --> |HTTP POST <br>/logs <br>POST /metrics| B[Ingestion API <br>FastAPI <br>Port 8000]
    B --> |XADD| C[Redis Streams: <br>logs_stream<br>metrics_stream]
    C --> |XREADGROUP <br>consumer group: workers| D[Worker <br>Validate event <br>Batch DB insert <br>ACK after persistence]
    D --> |SQL| E[TimescaleDB PostgreSQL-compatible:<br> logs hypertable<br> metrics hypertable]
    E -->|"SQL queries<br>time_bucket()"| F[Query API FastAPI Port 8001]
    F --> |HTTP GET| G[Dashboard Next.js + React Port 3000<br><br>Latency chart<br>Error-rate chart<br>Recent logs]
```

---

# Why this architecture?

A telemetry system has a different workload from a normal CRUD application.

Applications may suddenly emit hundreds or thousands of telemetry events during an incident. Writing each incoming event directly to the database would tightly couple application ingestion speed to database performance.

This project therefore introduces **Redis Streams as a buffer** between ingestion and persistence.

```mermaid
flowchart LR
A[Application] --> B[Ingestion API]
B --> C[Redis Stream]
C --> D[Worker]
D --> E[TimescaleDB]
```

The ingestion API only needs to validate the event and enqueue it.

The worker can then process telemetry independently.

This separation provides several useful system-design properties:

- ingestion and database persistence are decoupled;
- short traffic bursts can be absorbed by Redis;
- database writes can be grouped into batches;
- workers can acknowledge events after persistence;
- the API layer remains small;
- telemetry storage is optimized for time-based queries;
- the dashboard never talks directly to the database;
- ingestion and querying can evolve independently.

---

# End-to-end workflow

## Log workflow

```mermaid
flowchart TD
    A[Application] -->|POST /logs| B[Ingestion API]
    B -->|Pydantic validation<br>UUID + UTC timestamp| C[Redis]
    C -->|XADD logs_stream| D[logs_stream]
    D -->|XREADGROUP| E[Worker]
    E -->|LogEvent validation<br>batch INSERT| F[TimescaleDB]
    F --> G[logs hypertable]
    G -->|SELECT| H[Query API]
    H -->|GET /logs| I[Dashboard]
```

## Metric workflow

```mermaid
flowchart TD
    A["Application"] -->|"POST /metrics"| B["Ingestion API"]
    B -->|"Pydantic validation"| C["Redis"]
    C -->|"XADD metrics_stream"| D["metrics_stream"]
    D -->|"XREADGROUP"| E["Worker"]
    E -->|"MetricEvent validation<br>batch INSERT"| F["TimescaleDB"]
    F --> G["metrics hypertable"]
    G -->|"time_bucket&#40;&#41;<br>AVG / MIN / MAX"| H["Query API"]
    H -->|"GET /metrics"| I["Dashboard"]
    I --> J["Request Latency"]
    I --> K["Error Rate"]
```

---

# Tech stack

| Component | Technology | Responsibility |
|---|---|---|
| Backend language | Python | Ingestion, worker, querying, simulation |
| API framework | FastAPI | HTTP ingestion and query APIs |
| Validation | Pydantic | Structured telemetry models |
| Settings | pydantic-settings | Database and Redis configuration |
| Message buffer | Redis Streams | Temporary telemetry queue |
| Redis client | redis-py | Stream publishing and consumption |
| Database | TimescaleDB / PostgreSQL | Durable log and metric storage |
| Database client | Psycopg 3 | PostgreSQL access |
| Time-series aggregation | TimescaleDB `time_bucket()` | Metric aggregation |
| HTTP client | HTTPX | Synthetic traffic generation |
| Dashboard | Next.js | Web application |
| UI | React | Dashboard components |
| Language | TypeScript | Dashboard implementation |
| Charts | Recharts | Metric visualization |
| Styling | Tailwind CSS | Dashboard styling |
| Infrastructure | Docker Compose | Local Redis and TimescaleDB |


---

# Project structure

```text
observability-tool/
│
├── common/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   └── redis_client.py
│
├── ingestion_api/
│   └── main.py
│
├── worker/
│   ├── db.py
│   └── main.py
│
├── query_api/
│   ├── __init__.py
│   ├── db.py
│   └── main.py
│
├── traffic_generator/
│   └── main.py
│
├── dashboard/
│   ├── app/
│   │   ├── dashboard-client.tsx
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── components/
│   │   ├── LogTable.tsx
│   │   └── MetricChart.tsx
│   │
│   ├── lib/
│   │   └── api.ts
│   │
│   ├── public/
│   ├── package.json
│   ├── package-lock.json
│   ├── next.config.ts
│   ├── postcss.config.mjs
│   ├── eslint.config.mjs
│   └── tsconfig.json
│
├── sql/
│   └── complete_setup.sql
│
├── docker-compose.yml
├── requirements.txt
├── .gitignore
├── license.txt
└── README.md
```

---

# Responsibility of each component

| Component | Responsibility |
|---|---|
| `common/models.py` | Defines the common log and metric event schemas |
| `common/config.py` | Loads Redis and database configuration |
| `common/redis_client.py` | Publishes telemetry into Redis Streams |
| `ingestion_api/main.py` | HTTP interface for accepting telemetry |
| `worker/main.py` | Reads telemetry from Redis consumer groups |
| `worker/db.py` | Persists batches of events into TimescaleDB |
| `query_api/main.py` | Public read API for logs and metrics |
| `query_api/db.py` | Implements database queries and metric aggregation |
| `traffic_generator/main.py` | Generates realistic synthetic telemetry |
| `sql/complete_setup.sql` | Creates database tables, hypertables, and indexes |
| `dashboard/lib/api.ts` | Client for communicating with the query API |
| `dashboard/app/page.tsx` | Loads initial dashboard telemetry |
| `dashboard/app/dashboard-client.tsx` | Periodically refreshes live dashboard data |
| `dashboard/components/LogTable.tsx` | Displays recent log events |
| `dashboard/components/MetricChart.tsx` | Displays time-series metric charts |
| `docker-compose.yml` | Starts Redis and TimescaleDB locally |

---

# How each piece works

## 1. Shared telemetry models

`common/models.py` defines two event types.

### LogEvent

```python
class LogEvent(BaseModel):
    event_id: UUID
    time: datetime

    service: str
    level: str
    message: str
    metadata: Optional[dict]
```

`event_id` and `time` are automatically generated when they are not supplied.

Each event therefore receives:

- a UUID;
- a UTC timestamp;
- a service identifier;
- structured event information.

Example:

```json
{
  "service": "api-gateway",
  "level": "info",
  "message": "Request completed",
  "metadata": {
    "route": "/checkout",
    "status": 200
  }
}
```

---

### MetricEvent

```python
class MetricEvent(BaseModel):
    event_id: UUID
    time: datetime

    service: str
    metric_name: str
    value: float
    tags: Optional[dict]
```

Example:

```json
{
  "service": "api-gateway",
  "metric_name": "request_latency_ms",
  "value": 47.2,
  "tags": {
    "route": "/checkout"
  }
}
```

---

# 2. Ingestion API

The ingestion service is implemented in:

```text
ingestion_api/main.py
```

It exposes two telemetry endpoints.

```text
POST /logs
POST /metrics
```

The API validates incoming JSON using the shared Pydantic models.

After validation, the event is forwarded to Redis rather than written directly to PostgreSQL.

### Log ingestion
```mermaid
flowchart LR
A[POST /logs] --> B[LogEvent validation]
B --> C[publish_log&#40;&#41;]
C --> D[XADD logs_stream]
```

### Metric ingestion
```mermaid
flowchart LR
A[POST /metrics] --> B[MetricEvent validation]
B --> C[publish_metric&#40;&#41;]
C --> D[XADD metrics_stream]
```

Successful ingestion returns:

```http
202 Accepted
```

with the generated event ID.

Example response:

```json
{
  "event_id": "c0402645-6434-44ac-a83c-a26b757ae522"
}
```

If the event cannot be queued in Redis, the ingestion API returns:

```http
503 Service Unavailable
```

Invalid request bodies are handled by FastAPI/Pydantic and normally return:

```http
422 Unprocessable Entity
```

---

# 3. Redis Streams

Redis is used as a durable intermediate stream between the ingestion API and database worker.

There are two streams:

```text
logs_stream
metrics_stream
```

Publishing is handled by:

```text
common/redis_client.py
```

Conceptually:

```python
XADD logs_stream ...
XADD metrics_stream ...
```

Separating logs and metrics makes it possible to process the two telemetry types independently.

---

# 4. Worker

The worker is implemented in:

```text
worker/main.py
```

It creates the Redis consumer group:

```text
workers
```

for both telemetry streams.

The current consumer is named:

```text
worker-1
```

The worker uses Redis `XREADGROUP` to receive events.
```mermaid
flowchart TD
   A[Redis Stream] --> |XREADGROUP| B[Worker]
   B --> C[1. deserialize JSON]
   B --> D[2. validate Pydantic model]
   B --> E[3. insert database batch]
   B --> F[4. XACK]

```

The worker requests up to:

```text
100 messages
```

per Redis read and blocks for:

```text
500 ms
```

while waiting for telemetry.

---

## Persistence-before-acknowledgement

An important property of the worker is the order of operations.

```mermaid
flowchart TD
    A["Read message"] --> B["Validate"]
    B --> C["Write to DB"]
    C --> D["Commit"]
    D --> E["XACK"]
```

Redis messages are acknowledged after database insertion succeeds.

This avoids intentionally acknowledging an event before attempting durable persistence.

---

# 5. Batch database insertion

Database persistence is implemented in:

```text
worker/db.py
```

Logs and metrics are inserted using Psycopg `executemany()`.

For logs:

```sql
INSERT INTO logs (...)
VALUES (...)
ON CONFLICT (event_id, time) DO NOTHING;
```

Metrics use the same duplicate-protection strategy.

The `(event_id, time)` unique indexes allow an identical event to be safely ignored if the same serialized telemetry event is inserted again.

---

# 6. TimescaleDB

Telemetry is stored in TimescaleDB.

TimescaleDB is PostgreSQL-compatible but adds functionality intended for time-series workloads.

The project creates two hypertables:

```text
logs
metrics
```

The timestamp column is:

```text
time
```

for both tables.

This allows telemetry to be efficiently organized and queried by time.

---

# Database schema

## `logs`

| Column | Type | Purpose |
|---|---|---|
| `event_id` | UUID | Event identifier |
| `time` | TIMESTAMPTZ | Event time |
| `service` | TEXT | Producing service |
| `level` | TEXT | Log severity |
| `message` | TEXT | Log message |
| `metadata` | JSONB | Optional structured metadata |

The table is converted into a TimescaleDB hypertable using:

```sql
SELECT create_hypertable('logs', 'time');
```

Index:

```text
(service, time DESC)
```

Unique index:

```text
(event_id, time)
```

---

## `metrics`

| Column | Type | Purpose |
|---|---|---|
| `event_id` | UUID | Metric event identifier |
| `time` | TIMESTAMPTZ | Metric timestamp |
| `service` | TEXT | Producing service |
| `metric_name` | TEXT | Metric identifier |
| `value` | DOUBLE PRECISION | Numeric metric value |
| `tags` | JSONB | Optional structured labels |

The table becomes a TimescaleDB hypertable using:

```sql
SELECT create_hypertable('metrics', 'time');
```

Index:

```text
(service, metric_name, time DESC)
```

Unique index:

```text
(event_id, time)
```

---

# 7. Query API

The query layer is intentionally separated from telemetry ingestion.

It is implemented in:

```text
query_api/
```

and normally runs on:

```text
http://localhost:8001
```

The dashboard only communicates with this API.

It does not directly connect to TimescaleDB.

---

## Log queries

Endpoint:

```http
GET /logs
```

Supported query parameters:

| Parameter | Description | Default |
|---|---|---:|
| `service` | Filter by service | none |
| `level` | Filter by log level | none |
| `since_minutes` | Look-back period | 60 |
| `since` | Explicit timestamp | none |
| `limit` | Maximum log records | 100 |

Example:

```bash
curl "http://localhost:8001/logs?service=api-gateway&level=error&since_minutes=60&limit=100"
```

The database query orders logs by newest first.

```sql
ORDER BY time DESC
```

---

## Metric queries

Endpoint:

```http
GET /metrics
```

Supported parameters:

| Parameter | Description | Default |
|---|---|---:|
| `service` | Filter by service | none |
| `metric_name` | Filter by metric | none |
| `since_minutes` | Look-back period | 60 |
| `bucket_minutes` | Aggregation interval | 1 |

Example:

```bash
curl "http://localhost:8001/metrics?service=api-gateway&metric_name=request_latency_ms&since_minutes=60&bucket_minutes=1"
```

---

# Metric aggregation

TimescaleDB performs metric aggregation using:

```sql
time_bucket()
```

For every time bucket, the query calculates:

```text
AVG(value)
MAX(value)
MIN(value)
```

Conceptually:

```sql
SELECT
    time_bucket(bucket_width, time) AS bucket,
    avg(value) AS avg_value,
    max(value) AS max_value,
    min(value) AS min_value
FROM metrics
...
GROUP BY bucket
ORDER BY bucket;
```

The API therefore returns data similar to:

```json
[
  {
    "bucket": "2026-09-04T03:20:00Z",
    "avg_value": 48.3,
    "max_value": 63.2,
    "min_value": 39.4
  }
]
```

This means the browser does not need to download every raw metric point to create its charts.

---

# 8. Dashboard

The web dashboard is located in:

```text
dashboard/
```

and is built using:

```text
Next.js
React
TypeScript
Tailwind CSS
Recharts
```

The dashboard currently displays:

```text
┌──────────────────────────────────────────────┐
│            Observability Dashboard           │
├──────────────────────┬───────────────────────┤
│                      │                       │
│   Request Latency    │      Error Rate       │
│       Chart          │        Chart          │
│                      │                       │
├──────────────────────┴───────────────────────┤
│                                              │
│                 Recent Logs                  │
│                                              │
│   Time     Service       Level     Message   │
│   ...      api-gateway   INFO      ...       │
│   ...      payments      ERROR     ...       │
│                                              │
└──────────────────────────────────────────────┘
```

---

## Initial dashboard load

When the dashboard page loads, it retrieves:

- the last 60 minutes of logs;
- the last 60 minutes of `request_latency_ms`;
- the last 60 minutes of `error_rate`.

These are loaded on the server before the client dashboard component is rendered.

---

## Live refresh

After the initial load, the client refreshes data every:

```text
5 seconds
```

New logs are requested using the timestamp of the previous fetch.

The client keeps up to:

```text
200 recent logs
```

in memory.

Metric charts are refreshed using approximately the latest:

```text
10 minutes
```

of data with:

```text
1-minute buckets
```

---

## Dashboard charts

Two metric charts currently exist.

### Request latency

Metric:

```text
request_latency_ms
```

Display:

```text
Request Latency (ms)
```

### Error rate

Metric:

```text
error_rate
```

Display:

```text
Error Rate
```

The charts currently plot:

```text
avg_value
```

for each TimescaleDB time bucket.

---

# 9. Traffic generator

The project includes:

```text
traffic_generator/main.py
```

to demonstrate the platform without requiring external applications.

It simulates three services:

```text
auth-service
payments-service
api-gateway
```

For each service it continuously produces:

```text
logs
request_latency_ms
error_rate
```

and sends them to:

```text
http://localhost:8000
```

---

## Normal state

During normal operation, generated telemetry approximately represents:

```text
Log levels:
  mostly info
  occasional warn

Latency:
  around 50 ms

Error rate:
  approximately 0–2%
```

---

## Incident state

The generator occasionally places a simulated service into an incident state.

During an incident it generates behavior such as:

```text
Log levels:
  warn / error

Latency:
  approximately 400 ms

Error rate:
  approximately 10–40%

Traffic interval:
  faster than normal
```

This creates visible changes in the dashboard and provides a convenient way to test the telemetry pipeline.

---

# Running locally

## Prerequisites

Install:

- Git
- Python 3.10 or newer
- Docker with Docker Compose
- Node.js 20.9 or newer
- npm

The dashboard uses Next.js 16, which requires Node.js 20.9+.

---

## 1. Clone the repository

```bash
git clone https://github.com/CowGivesMilk/observability-tool.git
cd observability-tool
```

---

## 2. Create a Python virtual environment

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

# 4. Start Redis and TimescaleDB

```bash
docker compose up -d
```

The Compose configuration starts:

| Service | Host port |
|---|---:|
| TimescaleDB | `5432` |
| Redis | `6379` |

Check them with:

```bash
docker compose ps
```

---

# 5. Initialize TimescaleDB

The database configured by Docker Compose is:

```text
Database: observability
Username: obs
Password: obs
Port:     5432
```

Ensure the TimescaleDB extension is enabled:

```bash
docker compose exec timescaledb \
  psql -U obs -d observability \
  -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

Then apply the schema.

### Linux / macOS / Git Bash

```bash
docker compose exec -T timescaledb \
  psql -U obs -d observability \
  < sql/complete_setup.sql
```

### Windows PowerShell

```powershell
Get-Content .\sql\complete_setup.sql |
    docker compose exec -T timescaledb psql -U obs -d observability
```

The setup script creates:

```text
logs hypertable
metrics hypertable
service/time indexes
event UUID columns
event uniqueness indexes
```

> `complete_setup.sql` is intended for initial database setup and is not currently written as a fully idempotent migration script. Re-running it against an already initialized database may report that tables or indexes already exist.

---

# 6. Configure environment variables

Configuration is loaded from:

```text
common/config.py
```

Default values already match the included Docker Compose configuration.

You can therefore run the project without a `.env` file when using the defaults.

To override configuration, create:

```text
.env
```

at the project root.

Example:

```env
DB_URL=postgresql://obs:obs@localhost:5432/observability
REDIS_HOST=localhost
REDIS_PORT=6379
```

The defaults are equivalent to:

```text
PostgreSQL:
postgresql://obs:obs@localhost:5432/observability

Redis:
localhost:6379
```

---

# 7. Start the ingestion API

Open a terminal at the repository root with the Python environment activated.

Run:

```bash
python -m uvicorn ingestion_api.main:app --reload --port 8000
```

The ingestion API is now available at:

```text
http://localhost:8000
```

Interactive FastAPI documentation:

```text
http://localhost:8000/docs
```

---

# 8. Start the worker

Open another terminal.

Activate the same Python virtual environment and run:

```bash
python -m worker.main
```

The worker will:

```text
connect to Redis
        │
        ├── create/check consumer groups
        │
        ├── read logs_stream
        │
        ├── read metrics_stream
        │
        ├── validate events
        │
        ├── persist batches
        │
        └── acknowledge persisted Redis messages
```

---

# 9. Start the query API

Open another terminal and run:

```bash
python -m uvicorn query_api.main:app --reload --port 8001
```

The API is available at:

```text
http://localhost:8001
```

Interactive API documentation:

```text
http://localhost:8001/docs
```

The current dashboard expects the query API at this port.

---

# 10. Install dashboard dependencies

Open another terminal:

```bash
cd dashboard
npm ci
```

If you are intentionally modifying dependencies instead of reproducing the lock file, use:

```bash
npm install
```

---

# 11. Start the dashboard

From the `dashboard` directory:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

The Query API currently allows CORS requests from this origin.

---

# 12. Start synthetic traffic

Return to the repository root in another terminal.

Run:

```bash
python -m traffic_generator.main
```

The generator will continuously submit telemetry to:

```text
http://localhost:8000
```

You should begin seeing:

- logs appear in the dashboard;
- request-latency data populate;
- error-rate data populate;
- occasional simulated incidents.

---

# Complete local process layout

When everything is running, the system should look like this:

```text
Terminal 1
──────────
docker compose
    ├── Redis :6379
    └── TimescaleDB :5432


Terminal 2
──────────
python -m uvicorn ingestion_api.main:app --reload --port 8000


Terminal 3
──────────
python -m worker.main


Terminal 4
──────────
python -m uvicorn query_api.main:app --reload --port 8001


Terminal 5
──────────
cd dashboard
npm run dev
              → http://localhost:3000


Terminal 6
──────────
python -m traffic_generator.main
```

---

# Quick API test

You do not need to run the traffic generator to test the pipeline.

Telemetry can be sent manually with `curl`.

---

## Send a log

```bash
curl -X POST http://localhost:8000/logs \
  -H "Content-Type: application/json" \
  -d '{
    "service": "api-gateway",
    "level": "info",
    "message": "Request completed",
    "metadata": {
      "route": "/checkout",
      "status": 200
    }
  }'
```

Expected response:

```json
{
  "event_id": "<generated-uuid>"
}
```

HTTP status:

```text
202 Accepted
```

---

## Send a metric

```bash
curl -X POST http://localhost:8000/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "service": "api-gateway",
    "metric_name": "request_latency_ms",
    "value": 47.2,
    "tags": {
      "route": "/checkout"
    }
  }'
```

---

## Send an error-rate metric

```bash
curl -X POST http://localhost:8000/metrics \
  -H "Content-Type: application/json" \
  -d '{
    "service": "api-gateway",
    "metric_name": "error_rate",
    "value": 0.03
  }'
```

---

# Querying telemetry manually

## Retrieve recent logs

```bash
curl "http://localhost:8001/logs"
```

---

## Retrieve logs for one service

```bash
curl "http://localhost:8001/logs?service=api-gateway"
```

---

## Retrieve only error logs

```bash
curl "http://localhost:8001/logs?level=error"
```

---

## Retrieve service errors

```bash
curl "http://localhost:8001/logs?service=payments-service&level=error&since_minutes=30"
```

---

## Query request latency

```bash
curl "http://localhost:8001/metrics?metric_name=request_latency_ms&since_minutes=60&bucket_minutes=1"
```

---

## Query latency for a specific service

```bash
curl "http://localhost:8001/metrics?service=api-gateway&metric_name=request_latency_ms&since_minutes=60&bucket_minutes=5"
```

---

# Inspecting Redis

You can inspect the streams directly.

Enter Redis CLI:

```bash
docker compose exec redis redis-cli
```

Check log-stream length:

```redis
XLEN logs_stream
```

Check metric-stream length:

```redis
XLEN metrics_stream
```

Inspect recent log events:

```redis
XREVRANGE logs_stream + - COUNT 5
```

Inspect the worker consumer group:

```redis
XINFO GROUPS logs_stream
```

Inspect consumers:

```redis
XINFO CONSUMERS logs_stream workers
```

---

# Inspecting TimescaleDB

Open PostgreSQL:

```bash
docker compose exec timescaledb psql -U obs -d observability
```

Check logs:

```sql
SELECT
    time,
    service,
    level,
    message
FROM logs
ORDER BY time DESC
LIMIT 20;
```

Check metrics:

```sql
SELECT
    time,
    service,
    metric_name,
    value
FROM metrics
ORDER BY time DESC
LIMIT 20;
```

Count telemetry:

```sql
SELECT COUNT(*) FROM logs;
SELECT COUNT(*) FROM metrics;
```

Inspect hypertables:

```sql
SELECT *
FROM timescaledb_information.hypertables;
```

Exit:

```text
\q
```

---

# Configuration

The Python services currently share the following configuration.

| Setting | Default | Purpose |
|---|---|---|
| `DB_URL` | `postgresql://obs:obs@localhost:5432/observability` | PostgreSQL/TimescaleDB connection |
| `REDIS_HOST` | `localhost` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |

Some application addresses are currently defined directly in code.

| Component | Current address |
|---|---|
| Ingestion API | `http://localhost:8000` |
| Query API | `http://localhost:8001` |
| Dashboard | `http://localhost:3000` |
| TimescaleDB | `localhost:5432` |
| Redis | `localhost:6379` |

The traffic generator currently sends events to port `8000`, and the dashboard currently queries port `8001`.

---

# Data-flow guarantees

The current implementation contains several useful reliability mechanisms.

## Redis buffering

The ingestion endpoint does not synchronously insert telemetry into TimescaleDB.

Redis Streams absorb telemetry before persistence.

---

## Consumer groups

The worker reads Redis through a consumer group rather than simply polling the complete stream.

This provides the foundation for coordinating stream consumers.

---

## Acknowledge after persistence

Events are acknowledged after database insertion succeeds.
```mermaid
flowchart LR
   A[Redis Event] --> B[Database insert]
   B --> C[Commit]
   C --> D[XACK]
```


---

## Duplicate-safe inserts

The database uses:

```sql
ON CONFLICT (event_id, time) DO NOTHING
```

together with unique indexes on:

```text
(event_id, time)
```

so replaying the same serialized telemetry event does not create an identical duplicate row.

---

# Dashboard data semantics

The current dashboard intentionally presents an overall system-level view.

It queries:

```text
request_latency_ms
error_rate
```

without selecting an individual service.

As a result, values from matching metrics across services are aggregated together into their respective time buckets.

This makes the current dashboard useful for viewing the overall behavior of the synthetic system.

Service-specific dashboard filtering can be added later using the existing `service` query parameter supported by the Query API.

---

# Development checks

The project does not currently include a committed automated backend test suite.

Useful development checks include the following.

## Python compile check

From the project root:

```bash
python -m compileall \
  common \
  ingestion_api \
  worker \
  query_api \
  traffic_generator
```

---

## Dashboard lint

```bash
cd dashboard
npm run lint
```

---

## Dashboard build

```bash
npm run build
```

---

## End-to-end smoke test

A practical system test is:

```text
1. Start Redis and TimescaleDB
2. Start ingestion API
3. Start worker
4. Start query API
5. POST a log
6. POST a metric
7. Query the events from port 8001
8. Confirm the dashboard displays them
```

This exercises the complete telemetry path:

```text
HTTP
 → FastAPI
 → Redis
 → Worker
 → TimescaleDB
 → Query API
 → Dashboard
```

---

# Stopping the project

Stop the Python services and dashboard with:

```text
Ctrl+C
```

Stop infrastructure:

```bash
docker compose down
```

This keeps the Redis and TimescaleDB volumes.

To completely remove local database and Redis data:

```bash
docker compose down -v
```

> `-v` permanently deletes the local Docker volumes and all telemetry stored in them.

---

# Resetting the database

If you want a completely fresh environment:

```bash
docker compose down -v
docker compose up -d
```

Then enable TimescaleDB again if required:

```bash
docker compose exec timescaledb \
  psql -U obs -d observability \
  -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

and re-run:

```text
sql/complete_setup.sql
```

---

# Troubleshooting

## `create_hypertable` does not exist

Ensure the TimescaleDB extension is enabled:

```bash
docker compose exec timescaledb \
  psql -U obs -d observability \
  -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

---

## Ingestion API returns `503`

Check Redis:

```bash
docker compose ps
```

Test it:

```bash
docker compose exec redis redis-cli PING
```

Expected:

```text
PONG
```

---

## Worker does not persist telemetry

Check:

```text
Redis is running
TimescaleDB is running
database schema has been initialized
worker is running
DB_URL is correct
```

Inspect Redis:

```bash
docker compose exec redis redis-cli XLEN logs_stream
```

If events are in Redis but not PostgreSQL, inspect the worker terminal for database or event-validation errors.

---

## Traffic generator reports connection errors

The traffic generator expects the ingestion API at:

```text
http://localhost:8000
```

Start it with:

```bash
python -m uvicorn ingestion_api.main:app --reload --port 8000
```

---

## Dashboard cannot load telemetry

The dashboard currently expects the query API at:

```text
http://localhost:8001
```

Start:

```bash
python -m uvicorn query_api.main:app --reload --port 8001
```

Then verify:

```text
http://localhost:8001/logs
```

---

## CORS errors

The Query API currently permits the dashboard origin:

```text
http://localhost:3000
```

If you run the dashboard on a different host or port, update the Query API CORS configuration.

---

## SQL reports that tables already exist

`complete_setup.sql` is currently an initialization script rather than a versioned migration system.

If the database is already initialized, either continue using the existing schema or reset the Docker database volume before applying the script again.

---

# Known limitations

This repository currently focuses on demonstrating the fundamental observability pipeline rather than providing a production monitoring platform.

### Redis pending-message recovery

The worker reads new messages using a Redis consumer group and acknowledges them after persistence, but it does not currently implement explicit stale pending-message recovery using mechanisms such as `XAUTOCLAIM`.

A worker failure after reading an event but before acknowledging it can therefore leave that event in the pending entries list until recovery logic is added.

---

### Static worker identity

The consumer name is currently:

```text
worker-1
```

Running multiple workers should eventually use unique consumer names.

---

### No dead-letter stream

Events that repeatedly fail validation or database persistence do not currently have a dedicated dead-letter stream.

---

### Infrastructure-only Docker Compose

Docker Compose currently starts only:

```text
TimescaleDB
Redis
```

The Python APIs, worker, traffic generator, and Next.js dashboard are started separately on the host.

---

### Hard-coded application addresses

The dashboard query URL and traffic-generator ingestion URL currently use localhost addresses directly in application code.

These should become environment-configurable before containerized or remote deployment.

---

### Development-oriented CORS configuration

The Query API currently allows:

```text
http://localhost:3000
```

for development.

Production deployments would require appropriate origin configuration.

---

### No authentication

Neither ingestion nor query endpoints currently require authentication.

Any client with network access can submit or retrieve telemetry.

---

### No multi-tenancy

Events are separated by `service`, but there is currently no concept of:

```text
organization
tenant
project
environment
API key
```

---

### No retention policy

TimescaleDB retention is not currently configured.

Telemetry will continue accumulating until it is manually removed.

---

### No compression policy

TimescaleDB compression policies are not currently configured.

---

### Logs are not full-text searchable

Log querying currently supports:

```text
service
level
time
limit
```

but not full-text message searching.

---

### No traces

The current telemetry model supports:

```text
logs
metrics
```

but not distributed traces or spans.

---

### No alerting

The project visualizes incidents but does not yet implement alert rules or notifications.

---

### No service-specific dashboard controls

The Query API supports service filtering, but the current dashboard shows aggregate metric behavior across services.

---

### No production deployment configuration

The repository does not currently include:

```text
TLS termination
reverse proxy
authentication
container images for application services
orchestration manifests
production secrets management
```

---

### No automated backend test suite

The current repository does not yet contain a dedicated unit/integration/end-to-end backend test suite.

---

# Possible extensions

Natural next steps for the project include:

1. **Pending-event recovery**
   - implement `XAUTOCLAIM`;
   - retry abandoned Redis events;
   - introduce a dead-letter stream.

2. **Horizontal worker scaling**
   - dynamic consumer names;
   - multiple worker instances;
   - worker health monitoring.

3. **Containerize every service**
   - ingestion API;
   - worker;
   - query API;
   - dashboard;
   - traffic generator.

4. **Centralized environment configuration**
   - API URLs;
   - ports;
   - CORS;
   - Redis streams;
   - worker identifiers.

5. **TimescaleDB lifecycle policies**
   - retention;
   - compression;
   - continuous aggregates.

6. **Dashboard filtering**
   - service selector;
   - time range;
   - log level;
   - metric selector.

7. **Log search**
   - message search;
   - metadata filtering;
   - pagination.

8. **Alerting**
   - latency thresholds;
   - error-rate thresholds;
   - alert cooldowns;
   - webhook notifications.

9. **Distributed tracing**
   - trace IDs;
   - span IDs;
   - OpenTelemetry ingestion;
   - log/trace correlation.

10. **Authentication and multi-tenancy**
    - API keys;
    - project ownership;
    - tenant isolation.

11. **Automated testing**
    - Pydantic model tests;
    - ingestion API tests;
    - Redis integration tests;
    - database integration tests;
    - query API tests;
    - worker failure/recovery tests;
    - full pipeline tests.

12. **CI/CD**
    - Python linting;
    - TypeScript linting;
    - frontend build;
    - automated tests;
    - container builds.

13. **Operational health endpoints**
    - `/health`;
    - Redis connectivity;
    - database connectivity;
    - worker status.

14. **Observing the observability platform**
    - ingestion throughput;
    - Redis queue depth;
    - worker processing rate;
    - database-write latency;
    - failed-event count.

---

# Core concepts demonstrated

This project is intentionally small enough to understand end-to-end while still demonstrating several important backend and distributed-system concepts:

```text
Structured telemetry
Pydantic validation
FastAPI service separation
Asynchronous ingestion
Redis Streams
Consumer groups
Buffered event processing
Batch persistence
Idempotent database writes
Time-series databases
TimescaleDB hypertables
Time-bucket aggregation
Service-oriented architecture
Separation of writes and reads
Live dashboard polling
Synthetic fault generation
```

The important part of the project is therefore not only the dashboard, but the entire telemetry pipeline.

It demonstrates the full telemetry lifecycle:

```mermaid
flowchart TD
    A["Generate"] --> B["Ingest"]
    B --> C["Validate"]
    C --> D["Buffer"]
    D --> E["Consume"]
    E --> F["Persist"]
    F --> G["Aggregate"]
    G --> H["Query"]
    H --> I["Visualize"]
```

---
# License

This project is licensed under the **MIT License**.

```text
Copyright 2026 Nimesh Poudel
```

See:

```text
license.txt
```

for the full license text.

---