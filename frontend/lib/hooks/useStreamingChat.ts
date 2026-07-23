/**
 * lib/hooks/useStreamingChat.ts
 *
 * Why this file exists:
 *   The browser's native EventSource only supports GET requests with no
 *   custom headers, but our /messages endpoint is a POST requiring a
 *   Bearer token. This hook instead uses fetch() with a ReadableStream
 *   reader and manually parses the `data: {...}\n\n` SSE framing —
 *   giving us POST + auth headers + streaming all at once.
 */

import { useCallback, useRef, useState } from "react";
import { useAuthStore } from "@/store/authStore";
import type { StreamEvent } from "@/types/chat";

interface UseStreamingChatResult {
  streamedText: string;
  isStreaming: boolean;
  error: string | null;
  sendMessage: (conversationId: string, content: string, model: string, documentIds?: string[]) => Promise<void>;
  stop: () => void;
}

export function useStreamingChat(
  onComplete?: (fullText: string, messageId: string | null) => void
): UseStreamingChatResult {
  const [streamedText, setStreamedText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  const sendMessage = useCallback(
    async (conversationId: string, content: string, model: string, documentIds: string[] = []) => {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
      const token = useAuthStore.getState().accessToken;
      const controller = new AbortController();
      abortRef.current = controller;

      setStreamedText("");
      setError(null);
      setIsStreaming(true);

      try {
        const response = await fetch(`${baseUrl}/conversations/${conversationId}/messages`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: token ? `Bearer ${token}` : "",
          },
          body: JSON.stringify({ content, model, document_ids: documentIds }),
          signal: controller.signal,
        });

        if (!response.body) throw new Error("No response stream");
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let accumulated = "";
        let finalMessageId: string | null = null;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() ?? ""; // keep the last (possibly incomplete) chunk in the buffer

          for (const line of lines) {
            if (!line.startsWith("data:")) continue;
            const event: StreamEvent & { error?: string } = JSON.parse(line.slice(5));

            if (event.error) {
              setError(event.error);
              continue;
            }
            if (event.text) {
              accumulated += event.text;
              setStreamedText(accumulated);
            }
            if (event.done) {
              finalMessageId = event.message_id;
            }
          }
        }

        onComplete?.(accumulated, finalMessageId);
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setError(err instanceof Error ? err.message : "Streaming failed");
        }
      } finally {
        setIsStreaming(false);
      }
    },
    [onComplete]
  );

  return { streamedText, isStreaming, error, sendMessage, stop };
}
