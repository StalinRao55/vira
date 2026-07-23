/**
 * types/chat.ts
 *
 * Why this file exists:
 *   Mirrors backend Pydantic response schemas (chat_schemas.py). Kept in
 *   sync manually for now - a codegen step (openapi-typescript against
 *   the backend's /openapi.json) is a reasonable later addition once the
 *   API stabilizes, noted here rather than adding tooling prematurely.
 */

export interface Conversation {
  id: string;
  title: string;
  is_archived: boolean;
  is_pinned: boolean;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  model_provider: string | null;
  model_name: string | null;
  token_count: number | null;
  is_edited: boolean;
  parent_message_id: string | null;
  created_at: string;
}

export interface StreamEvent {
  text: string;
  done: boolean;
  message_id: string | null;
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  status: "processing" | "ready" | "failed" | string;
  uploaded_at: string;
}

export interface UsageSummary {
  period_days: number;
  total_requests: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  estimated_cost_usd: number;
  average_latency_ms: number;
}
