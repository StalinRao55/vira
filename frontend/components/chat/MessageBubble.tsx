/**
 * components/chat/MessageBubble.tsx
 *
 * Why this file exists:
 *   Renders one message with markdown formatting and syntax-highlighted
 *   code blocks. User and assistant messages are styled distinctly (user:
 *   solid accent bubble, right-aligned; assistant: flush-left, no bubble,
 *   matching the "document, not a chat log" feel of assistant turns).
 */

"use client";

import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Copy, RotateCcw } from "lucide-react";
import type { Message } from "@/types/chat";

interface MessageBubbleProps {
  message: Message;
  onRegenerate?: () => void;
}

export function MessageBubble({ message, onRegenerate }: MessageBubbleProps) {
  const isUser = message.role === "user";

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content);
  };

  if (isUser) {
    return (
      <div className="flex justify-end px-4 py-2">
        <div className="max-w-[75%] rounded-lg bg-accent px-4 py-2.5 text-bg font-body">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="group px-4 py-3">
      <div className="max-w-[85%] font-body text-text">
        <ReactMarkdown
          components={{
            code({ className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || "");
              return match ? (
                <SyntaxHighlighter
                  style={oneDark}
                  language={match[1]}
                  PreTag="div"
                  customStyle={{ borderRadius: 10, fontFamily: "var(--font-mono)" }}
                >
                  {String(children).replace(/\n$/, "")}
                </SyntaxHighlighter>
              ) : (
                <code className="rounded bg-surface-raised px-1.5 py-0.5 font-mono text-sm" {...props}>
                  {children}
                </code>
              );
            },
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>
      <div className="mt-1 flex gap-2 opacity-0 transition-opacity group-hover:opacity-100">
        <button
          onClick={copyToClipboard}
          className="rounded p-1 text-text-muted hover:bg-surface-raised hover:text-text"
          aria-label="Copy message"
        >
          <Copy size={14} />
        </button>
        {onRegenerate && (
          <button
            onClick={onRegenerate}
            className="rounded p-1 text-text-muted hover:bg-surface-raised hover:text-text"
            aria-label="Regenerate response"
          >
            <RotateCcw size={14} />
          </button>
        )}
      </div>
    </div>
  );
}
