const QUERY_API_URL = "http://localhost:8001";
export type LogEntry = {
    time: string;
    service: string;
    level: string;
    message: string;
    metadata: Record<string, unknown> | null;
    event_id: string;
};
export type MetricBucket = {
    bucket: string;
    avg_value: number;
    max_value: number;
    min_value: number;
};
export async function fetchLogs(params: {
    service?: string;
    level?: string;
    since?: string;
    since_minutes?: number;
    limit?: number;
}): Promise<LogEntry[]> {
    const query = new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== undefined) as [string, string][]
    );
    const res = await fetch(`${QUERY_API_URL}/logs?${query}`, { cache: "no-store" });
    return res.json();
}
export async function fetchMetrics(params: {
    service?: string;
    metric_name?: string;
    since_minutes?: number;
    bucket_minutes?: number;
}): Promise<MetricBucket[]> {
    const query = new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== undefined) as [string, string][]
    );
    const res = await fetch(`${QUERY_API_URL}/metrics?${query}`, { cache: "no-store" });
    return res.json();
}