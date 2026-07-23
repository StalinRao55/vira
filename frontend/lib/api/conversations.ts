/**
 * lib/api/conversations.ts
 *
 * Why this file exists:
 *   Typed wrappers around the /conversations endpoints. Components call
 *   these instead of touching `api` directly, so the response shape is
 *   known at compile time and lives in one place if the backend changes.
 */

import { api } from "./client";
import type { Conversation } from "@/types/chat";

export async function listConversations(includeArchived = false): Promise<Conversation[]> {
  const { data } = await api.get<Conversation[]>("/conversations", { params: { include_archived: includeArchived } });
  return data;
}

export async function createConversation(): Promise<Conversation> {
  const { data } = await api.post<Conversation>("/conversations");
  return data;
}

export async function updateConversation(
  id: string,
  update: Partial<Pick<Conversation, "title" | "is_archived" | "is_pinned" | "is_favorite">>
): Promise<Conversation> {
  const { data } = await api.patch<Conversation>(`/conversations/${id}`, update);
  return data;
}

export async function deleteConversation(id: string): Promise<void> {
  await api.delete(`/conversations/${id}`);
}

export async function searchConversations(query: string): Promise<Conversation[]> {
  const { data } = await api.get<Conversation[]>("/conversations/search", { params: { q: query } });
  return data;
}
