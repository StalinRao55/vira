/**
 * app/(chat)/c/[conversationId]/page.tsx
 *
 * Why this file exists:
 *   The core chat screen: loads message history via TanStack Query,
 *   renders it with MessageBubble, and wires ChatInput to
 *   useStreamingChat. The streaming assistant reply is rendered as an
 *   extra "live" bubble while in flight, then folded into the real
 *   message list once the stream completes and history is refetched.
 */

"use client";

import { useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import { useStreamingChat } from "@/lib/hooks/useStreamingChat";
import { useUIStore } from "@/store/uiStore";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import type { Message } from "@/types/chat";

async function fetchMessages(conversationId: string): Promise<Message[]> {
  const { data } = await api.get<Message[]>(`/conversations/${conversationId}/messages`);
  return data;
}

async function uploadDocument(file: File): Promise<{ id: string; status: string }> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/documents", formData, { headers: { "Content-Type": "multipart/form-data" } });
  return data;
}

export default function ConversationPage() {
  const params = useParams<{ conversationId: string }>();
  const conversationId = params.conversationId;
  const queryClient = useQueryClient();
  const { selectedModel } = useUIStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: messages = [] } = useQuery({
    queryKey: ["messages", conversationId],
    queryFn: () => fetchMessages(conversationId),
    enabled: !!conversationId,
  });

  const { streamedText, isStreaming, error, sendMessage, stop } = useStreamingChat(() => {
    queryClient.invalidateQueries({ queryKey: ["messages", conversationId] });
    queryClient.invalidateQueries({ queryKey: ["conversations"] }); // title may have just been generated
  });

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamedText]);

  const handleSend = (content: string) => {
    sendMessage(conversationId, content, selectedModel);
  };

  const handleFileSelect = async (file: File) => {
    await uploadDocument(file);
    // A full build would surface this in an "attached documents" chip row
    // and pass its id into sendMessage's document_ids — wiring point noted
    // rather than expanded here to keep this phase focused.
  };

  return (
    <>
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl py-6">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isStreaming && streamedText && (
            <MessageBubble
              message={{
                id: "streaming",
                conversation_id: conversationId,
                role: "assistant",
                content: streamedText,
                model_provider: null,
                model_name: null,
                token_count: null,
                is_edited: false,
                parent_message_id: null,
                created_at: new Date().toISOString(),
              }}
            />
          )}
          {error && <p className="px-4 text-sm text-red-400">Error: {error}</p>}
          <div ref={scrollRef} />
        </div>
      </div>
      <ChatInput onSend={handleSend} onStop={stop} onFileSelect={handleFileSelect} isStreaming={isStreaming} />
    </>
  );
}
