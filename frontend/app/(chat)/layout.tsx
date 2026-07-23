/**
 * app/(chat)/layout.tsx
 *
 * Why this file exists:
 *   Route group layout: every page under (chat)/ gets the sidebar shell
 *   automatically, without affecting the URL (the group name in
 *   parentheses is stripped from the path — /c/[id], not /(chat)/c/[id]).
 */

import { Sidebar } from "@/components/layout/Sidebar";

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-bg">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
    </div>
  );
}
