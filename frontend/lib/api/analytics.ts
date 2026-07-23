import { api } from "./client";
import type { UsageSummary } from "@/types/chat";

export async function getUsageSummary(days = 30): Promise<UsageSummary> {
  const { data } = await api.get<UsageSummary>("/analytics/usage", { params: { days } });
  return data;
}
