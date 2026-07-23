"use client";

import { Check, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useUIStore } from "@/store/uiStore";
import { useAuthStore } from "@/store/authStore";

const models = ["gemini-3-flash", "gemini-2.5-flash", "gemini-2.5-pro"];

export default function SettingsPage() {
  const router = useRouter();
  const selectedModel = useUIStore((state) => state.selectedModel);
  const setSelectedModel = useUIStore((state) => state.setSelectedModel);
  const logout = useAuthStore((state) => state.logout);

  const handleLogout = () => {
    logout();
    router.replace("/login");
  };

  return (
    <div className="flex-1 overflow-y-auto bg-bg">
      <div className="mx-auto max-w-3xl px-6 py-6">
        <div className="border-b border-border pb-4">
          <h1 className="font-display text-2xl text-text">Settings</h1>
          <p className="mt-1 text-sm text-text-muted">Tune the chat experience and account session.</p>
        </div>

        <section className="mt-6">
          <h2 className="text-sm font-medium uppercase text-text-muted">Default Model</h2>
          <div className="mt-3 grid gap-2">
            {models.map((model) => (
              <button
                key={model}
                onClick={() => setSelectedModel(model)}
                className="flex items-center justify-between rounded-md border border-border bg-surface px-4 py-3 text-left text-sm text-text hover:bg-surface-raised"
              >
                <span>{model}</span>
                {selectedModel === model && <Check size={16} className="text-highlight" />}
              </button>
            ))}
          </div>
        </section>

        <section className="mt-8 border-t border-border pt-6">
          <h2 className="text-sm font-medium uppercase text-text-muted">Session</h2>
          <button
            onClick={handleLogout}
            className="mt-3 inline-flex items-center gap-2 rounded-md border border-border px-3 py-2 text-sm text-text hover:bg-surface"
          >
            <LogOut size={16} /> Sign out
          </button>
        </section>
      </div>
    </div>
  );
}
