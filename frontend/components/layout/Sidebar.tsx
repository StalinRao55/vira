/**
 * components/layout/Sidebar.tsx
 *
 * Why this file exists:
 *   The conversation list surface: search, pinned-first ordering (matches
 *   the backend's sort in list_by_user), and per-conversation actions
 *   (pin/favorite/archive/delete) as a hover-revealed menu.
 */

"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter, useParams, usePathname } from "next/navigation";
import {
  Archive,
  BarChart3,
  FileText,
  Link2,
  PanelLeftClose,
  Pin,
  Plus,
  Search,
  Settings,
  Star,
  Trash2,
} from "lucide-react";
import {
  listConversations,
  createConversation,
  updateConversation,
  deleteConversation,
  searchConversations,
} from "@/lib/api/conversations";
import { useUIStore } from "@/store/uiStore";
import type { Conversation } from "@/types/chat";

const navItems = [
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/share", label: "Share", icon: Link2 },
  { href: "/admin", label: "Admin", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const router = useRouter();
  const params = useParams();
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const [searchQuery, setSearchQuery] = useState("");

  const { data: conversations = [] } = useQuery({
    queryKey: ["conversations", searchQuery],
    queryFn: () => (searchQuery ? searchConversations(searchQuery) : listConversations()),
  });

  const createMutation = useMutation({
    mutationFn: createConversation,
    onSuccess: (conversation) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      router.push(`/c/${conversation.id}`);
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, update }: { id: string; update: Partial<Conversation> }) => updateConversation(id, update),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["conversations"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteConversation,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["conversations"] }),
  });

  if (!sidebarOpen) {
    return (
      <button
        onClick={toggleSidebar}
        className="flex h-full w-12 flex-col items-center border-r border-border bg-surface py-3 text-text-muted hover:text-text"
        aria-label="Open sidebar"
      >
        <PanelLeftClose size={18} className="rotate-180" />
      </button>
    );
  }

  return (
    <aside className="flex h-full w-72 flex-col border-r border-border bg-surface">
      <div className="flex items-center justify-between px-3 py-3">
        <span className="font-display text-lg text-text">VIRA</span>
        <button onClick={toggleSidebar} className="text-text-muted hover:text-text" aria-label="Collapse sidebar">
          <PanelLeftClose size={18} />
        </button>
      </div>

      <div className="px-3 pb-2">
        <button
          onClick={() => createMutation.mutate()}
          className="flex w-full items-center gap-2 rounded-md bg-accent px-3 py-2 text-sm font-medium text-bg hover:bg-accent-hover"
        >
          <Plus size={16} /> New chat
        </button>
      </div>

      <div className="grid gap-1 px-2 pb-3">
        {navItems.map(({ href, label, icon: Icon }) => (
          <button
            key={href}
            onClick={() => router.push(href)}
            className={`flex items-center gap-2 rounded-md px-2 py-2 text-sm hover:bg-surface-raised ${
              pathname === href ? "bg-surface-raised text-text" : "text-text-muted"
            }`}
          >
            <Icon size={15} /> {label}
          </button>
        ))}
      </div>

      <div className="px-3 pb-2">
        <div className="flex items-center gap-2 rounded-md border border-border bg-surface-raised px-2 py-1.5">
          <Search size={14} className="text-text-muted" />
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conversations"
            className="w-full bg-transparent text-sm text-text placeholder:text-text-muted focus:outline-none"
          />
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-2">
        {conversations.map((conversation) => (
          <div
            key={conversation.id}
            className={`group flex items-center justify-between rounded-md px-2 py-2 text-sm hover:bg-surface-raised ${
              params?.conversationId === conversation.id ? "bg-surface-raised" : ""
            }`}
          >
            <button onClick={() => router.push(`/c/${conversation.id}`)} className="flex-1 truncate text-left text-text">
              {conversation.is_pinned && <Pin size={11} className="mr-1 inline text-highlight" />}
              {conversation.title}
            </button>
            <div className="hidden gap-1 group-hover:flex">
              <button
                onClick={() => updateMutation.mutate({ id: conversation.id, update: { is_pinned: !conversation.is_pinned } })}
                className="text-text-muted hover:text-highlight"
                aria-label="Pin conversation"
              >
                <Pin size={13} />
              </button>
              <button
                onClick={() => updateMutation.mutate({ id: conversation.id, update: { is_favorite: !conversation.is_favorite } })}
                className="text-text-muted hover:text-highlight"
                aria-label="Favorite conversation"
              >
                <Star size={13} />
              </button>
              <button
                onClick={() => updateMutation.mutate({ id: conversation.id, update: { is_archived: true } })}
                className="text-text-muted hover:text-text"
                aria-label="Archive conversation"
              >
                <Archive size={13} />
              </button>
              <button
                onClick={() => deleteMutation.mutate(conversation.id)}
                className="text-text-muted hover:text-red-400"
                aria-label="Delete conversation"
              >
                <Trash2 size={13} />
              </button>
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
}
