/**
 * components/chat/__tests__/MessageBubble.test.tsx
 *
 * Why this file exists:
 *   Verifies MessageBubble renders differently for user vs assistant
 *   roles and that markdown content actually renders as formatted HTML,
 *   not raw text.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MessageBubble } from "../MessageBubble";
import type { Message } from "@/types/chat";

function makeMessage(overrides: Partial<Message>): Message {
  return {
    id: "1",
    conversation_id: "conv-1",
    role: "user",
    content: "Hello",
    model_provider: null,
    model_name: null,
    token_count: null,
    is_edited: false,
    parent_message_id: null,
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

describe("MessageBubble", () => {
  it("renders user messages as plain text in a bubble", () => {
    render(<MessageBubble message={makeMessage({ role: "user", content: "Hi there" })} />);
    expect(screen.getByText("Hi there")).toBeInTheDocument();
  });

  it("renders assistant messages with markdown formatting", () => {
    render(<MessageBubble message={makeMessage({ role: "assistant", content: "**bold text**" })} />);
    const bold = screen.getByText("bold text");
    expect(bold.tagName.toLowerCase()).toBe("strong");
  });

  it("shows a regenerate button only when onRegenerate is provided", () => {
    const { rerender } = render(<MessageBubble message={makeMessage({ role: "assistant", content: "answer" })} />);
    expect(screen.queryByLabelText("Regenerate response")).not.toBeInTheDocument();

    rerender(<MessageBubble message={makeMessage({ role: "assistant", content: "answer" })} onRegenerate={() => {}} />);
    expect(screen.getByLabelText("Regenerate response")).toBeInTheDocument();
  });
});
