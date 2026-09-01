import { LogEntry } from "@/lib/api";

const levelColors: Record<string, string> = {
    info: "bg-blue-950 text-blue-300 border border-blue-900",
    warn: "bg-yellow-950 text-yellow-300 border border-yellow-900",
    error: "bg-red-950 text-red-300 border border-red-900",
};

export default function LogTable({ logs }: { logs: LogEntry[] }) {
    return (
        <div className="rounded-lg border border-neutral-800 bg-neutral-900 overflow-hidden">
            <div className="max-h-[500px] overflow-y-auto">
                <table className="w-full text-sm">
                    <thead className="bg-neutral-950 sticky top-0">
                        <tr>
                            <th className="text-left px-4 py-2 font-medium text-neutral-500">Time</th>
                            <th className="text-left px-4 py-2 font-medium text-neutral-500">Service</th>
                            <th className="text-left px-4 py-2 font-medium text-neutral-500">Level</th>
                            <th className="text-left px-4 py-2 font-medium text-neutral-500">Message</th>
                        </tr>
                    </thead>
                    <tbody>
                        {logs.map((log) => (
                            <tr key={log.event_id} className="border-t border-neutral-800 hover:bg-neutral-800/50">
                                <td className="px-4 py-2 text-neutral-500 whitespace-nowrap">
                                    {new Date(log.time).toLocaleTimeString()}
                                </td>
                                <td className="px-4 py-2 font-medium text-neutral-200">{log.service}</td>
                                <td className="px-4 py-2">
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${levelColors[log.level] ?? "bg-neutral-800 text-neutral-300 border border-neutral-700"}`}>
                                        {log.level}
                                    </span>
                                </td>
                                <td className="px-4 py-2 text-neutral-300">{log.message}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {logs.length === 0 && (
                    <div className="text-center py-8 text-neutral-600">No logs yet</div>
                )}
            </div>
        </div>
    );
}