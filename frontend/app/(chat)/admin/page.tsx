"use client";

import { Activity, Clock, Coins, MessageSquareText } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getUsageSummary } from "@/lib/api/analytics";

export default function AdminPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["usage-summary", 30],
    queryFn: () => getUsageSummary(30),
  });

  const stats = [
    { label: "Requests", value: data?.total_requests ?? 0, icon: MessageSquareText },
    { label: "Prompt tokens", value: data?.total_prompt_tokens ?? 0, icon: Activity },
    { label: "Cost", value: `$${(data?.estimated_cost_usd ?? 0).toFixed(4)}`, icon: Coins },
    { label: "Avg latency", value: `${data?.average_latency_ms ?? 0} ms`, icon: Clock },
  ];

  return (
    <div className="flex-1 overflow-y-auto bg-bg">
      <div className="mx-auto max-w-5xl px-6 py-6">
        <div className="border-b border-border pb-4">
          <h1 className="font-display text-2xl text-text">Admin</h1>
          <p className="mt-1 text-sm text-text-muted">Usage snapshot for the current account.</p>
        </div>

        {isLoading ? (
          <div className="mt-6 text-sm text-text-muted">Loading usage...</div>
        ) : (
          <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map(({ label, value, icon: Icon }) => (
              <div key={label} className="rounded-md border border-border bg-surface p-4">
                <Icon size={18} className="text-highlight" />
                <p className="mt-4 text-2xl font-semibold text-text">{value}</p>
                <p className="mt-1 text-sm text-text-muted">{label}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
