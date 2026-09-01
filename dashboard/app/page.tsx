import { fetchLogs, fetchMetrics } from "@/lib/api";
import DashboardClient from "./dashboard-client";

export default async function Page() {
    const [initialLogs, initialLatency, initialErrorRate] = await Promise.all([
        fetchLogs({ since_minutes: 60, limit: 100 }),
        fetchMetrics({ metric_name: "request_latency_ms", since_minutes: 60, bucket_minutes: 1 }),
        fetchMetrics({ metric_name: "error_rate", since_minutes: 60, bucket_minutes: 1 }),
    ]);

    return (
        <DashboardClient
            initialLogs={initialLogs}
            initialLatency={initialLatency}
            initialErrorRate={initialErrorRate}
        />
    );
}