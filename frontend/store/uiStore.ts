/**
 * store/uiStore.ts
 *
 * Why this file exists:
 *   Purely client-side UI state that doesn't belong in server state
 *   (TanStack Query owns that) or auth. Sidebar open/closed, the
 *   currently selected model — things that reset naturally on reload and
 *   never need to hit the network.
 */

import { create } from "zustand";

interface UIState {
  sidebarOpen: boolean;
  selectedModel: string;
  toggleSidebar: () => void;
  setSelectedModel: (model: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  selectedModel: "gemini-3-flash",
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSelectedModel: (model) => set({ selectedModel: model }),
}));
