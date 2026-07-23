/**
 * app/page.tsx
 *
 * Why this file exists:
 *   The bare "/" route has no conversation to show — redirects to login if
 *   unauthenticated, or creates/opens a conversation if authenticated.
 */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { createConversation, listConversations } from "@/lib/api/conversations";

export default function RootPage() {
  const router = useRouter();
  const accessToken = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    if (!accessToken) {
      router.replace("/login");
      return;
    }
    (async () => {
      const conversations = await listConversations();
      if (conversations.length > 0) {
        router.replace(`/c/${conversations[0].id}`);
      } else {
        const conversation = await createConversation();
        router.replace(`/c/${conversation.id}`);
      }
    })();
  }, [accessToken, router]);

  return <div className="flex h-screen items-center justify-center bg-bg text-text-muted">Loading VIRA...</div>;
}
