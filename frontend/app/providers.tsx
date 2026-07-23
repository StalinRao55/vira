/**
 * app/providers.tsx
 *
 * Why this file exists:
 *   TanStack Query needs its QueryClient instantiated inside a client
 *   component (it holds React context) — standard Next.js App Router
 *   pattern for that.
 */

"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient({ defaultOptions: { queries: { staleTime: 30_000 } } }));
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
