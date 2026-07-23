"use client";

import { Copy, Link2 } from "lucide-react";

export default function SharePage() {
  const origin = typeof window === "undefined" ? "" : window.location.origin;
  const shareUrl = origin;

  return (
    <div className="flex-1 overflow-y-auto bg-bg">
      <div className="mx-auto max-w-3xl px-6 py-6">
        <div className="border-b border-border pb-4">
          <h1 className="font-display text-2xl text-text">Share</h1>
          <p className="mt-1 text-sm text-text-muted">Copy a workspace link.</p>
        </div>

        <div className="mt-6 rounded-md border border-border bg-surface p-4">
          <div className="flex items-center gap-2 text-sm text-text-muted">
            <Link2 size={16} /> Link
          </div>
          <div className="mt-3 flex gap-2">
            <input value={shareUrl} readOnly className="min-w-0 flex-1 rounded-md border border-border bg-bg px-3 py-2 text-sm text-text" />
            <button
              onClick={() => navigator.clipboard.writeText(shareUrl)}
              className="inline-flex items-center gap-2 rounded-md bg-accent px-3 py-2 text-sm font-medium text-bg hover:bg-accent-hover"
            >
              <Copy size={16} /> Copy
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
