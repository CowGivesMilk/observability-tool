"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { MetricBucket } from "@/lib/api";

export default function MetricChart({
    title,
    data,
    color = "#60a5fa",
    unit = "",
}: {
    title: string;
    data: MetricBucket[];
    color?: string;
    unit?: string;
}) {
    const formatted = data.map((d) => ({
        ...d,
        label: new Date(d.bucket).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    }));

    return (
        <div className="rounded-lg border border-neutral-800 bg-neutral-900 p-4">
            <h3 className="text-sm font-medium text-neutral-500 mb-3">{title}</h3>
            <ResponsiveContainer width="100%" height={220}>
                <LineChart data={formatted}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                    <XAxis dataKey="label" tick={{ fontSize: 12, fill: "#737373" }} stroke="#404040" />
                    <YAxis tick={{ fontSize: 12, fill: "#737373" }} stroke="#404040" unit={unit} />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: "#171717",
                            border: "1px solid #404040",
                            borderRadius: 8,
                        }}
                        labelStyle={{ color: "#a3a3a3", fontSize: 12 }}
                        itemStyle={{ color: "#e5e5e5" }}
                        formatter={(value) => {
                            const num = Number(value ?? 0);
                            return [`${num.toFixed(2)}${unit}`, "avg"];
                        }}
                    />
                    <Line type="monotone" dataKey="avg_value" stroke={color} strokeWidth={2} dot={false} />
                </LineChart>
            </ResponsiveContainer>
            {data.length === 0 && (
                <div className="text-center py-8 text-neutral-600 text-sm">No data yet</div>
            )}
        </div>
    );
}