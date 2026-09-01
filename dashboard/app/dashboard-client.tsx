"use client";

import { useState, useEffect, useRef } from "react";
import { fetchLogs, fetchMetrics, LogEntry, MetricBucket } from "@/lib/api";
import LogTable from "@/components/LogTable";
import MetricChart from "@/components/MetricChart";
type Props = {
    initialLogs: LogEntry[];
    initialLatency: MetricBucket[];
    initialErrorRate: MetricBucket[];
};

export default function DashboardClient({ initialLogs, initialLatency, initialErrorRate }: Props) {
    const [logs, setLogs] = useState(initialLogs);
    const [latency, setLatency] = useState(initialLatency);
    const [errorRate, setErrorRate] = useState(initialErrorRate);
    const lastLogFetch = useRef(new Date().toISOString());

    useEffect(() => {
        const interval = setInterval(async () => {
            const since = lastLogFetch.current;
            lastLogFetch.current = new Date().toISOString();

            const [newLogs, freshLatency, freshErrorRate] = await Promise.all([
                fetchLogs({ since_minutes: minutesSince(since), limit: 100 }),
                fetchMetrics({ metric_name: "request_latency_ms", since_minutes: 10, bucket_minutes: 1 }),
                fetchMetrics({ metric_name: "error_rate", since_minutes: 10, bucket_minutes: 1 }),
            ]);

            setLogs((prev) => [...newLogs, ...prev].slice(0, 200));
            setLatency(freshLatency);
            setErrorRate(freshErrorRate);
        }, 5000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="max-w-6xl mx-auto p-6 space-y-6">
            <h1 className="text-xl font-semibold text-neutral-100">Observability Dashboard</h1>

            <div className="grid grid-cols-2 gap-4">
                <MetricChart title="Request Latency (ms)" data={latency} color="#60a5fa" unit="ms" />
                <MetricChart title="Error Rate" data={errorRate} color="#f87171" unit="" />
            </div>

            <div>
                <h2 className="text-sm font-medium text-neutral-500 mb-2">Recent Logs</h2>
                <LogTable logs={logs} />
            </div>
        </div>
    );
}

function minutesSince(iso: string): number {
    return Math.max(1, Math.ceil((Date.now() - new Date(iso).getTime()) / 60000));
}