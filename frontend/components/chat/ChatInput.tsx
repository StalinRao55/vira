/**
 * components/chat/ChatInput.tsx
 *
 * Why this file exists:
 *   The input area: auto-growing textarea, Enter-to-send/Shift+Enter-for-
 *   newline, a stop button while streaming, and a file-upload affordance
 *   for RAG attachments. Kept as one component since these interactions
 *   are tightly coupled (e.g. disabling send while streaming).
 */

"use client";

import { useRef, useState, KeyboardEvent } from "react";
import { Send, Square, Paperclip } from "lucide-react";
import { useUIStore } from "@/store/uiStore";

interface ChatInputProps {
  onSend: (content: string) => void;
  onStop: () => void;
  onFileSelect: (file: File) => void;
  isStreaming: boolean;
}

const MODELS = [
  { id: "gemini-3-flash", label: "Gemini 3 Flash" },
  { id: "gpt-4o", label: "GPT-4o" },
  { id: "claude-sonnet", label: "Claude Sonnet" },
];

export function ChatInput({ onSend, onStop, onFileSelect, isStreaming }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { selectedModel, setSelectedModel } = useUIStore();

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    }
  };

  const handleSend = () => {
    if (!value.trim() || isStreaming) return;
    onSend(value.trim());
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-border bg-surface px-4 py-3">
      <div className="mx-auto flex max-w-3xl flex-col gap-2 rounded-lg border border-border bg-surface-raised p-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Message VIRA..."
          rows={1}
          className="max-h-[200px] resize-none bg-transparent px-2 py-1.5 font-body text-text placeholder:text-text-muted focus:outline-none"
        />
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="rounded p-1.5 text-text-muted hover:bg-bg hover:text-text"
              aria-label="Attach file"
            >
              <Paperclip size={16} />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.docx,.txt,.md"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) onFileSelect(file);
              }}
            />
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="rounded bg-transparent px-1 py-0.5 text-sm text-text-muted hover:text-text focus:outline-none"
            >
              {MODELS.map((m) => (
                <option key={m.id} value={m.id} className="bg-surface">
                  {m.label}
                </option>
              ))}
            </select>
          </div>

          {isStreaming ? (
            <button
              onClick={onStop}
              className="flex items-center gap-1.5 rounded-md bg-surface px-3 py-1.5 text-sm text-text hover:bg-bg"
            >
              <Square size={14} /> Stop
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!value.trim()}
              className="flex items-center gap-1.5 rounded-md bg-accent px-3 py-1.5 text-sm text-bg hover:bg-accent-hover disabled:opacity-40"
            >
              <Send size={14} /> Send
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
