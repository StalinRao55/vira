/**
 * store/authStore.ts
 *
 * Why this file exists:
 *   Holds the access/refresh tokens client-side. Persisted to
 *   localStorage (via zustand's persist middleware) so a page refresh
 *   doesn't log the user out — api/client.ts reads from this store
 *   directly (outside React) to attach the Authorization header.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  setTokens: (accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      logout: () => set({ accessToken: null, refreshToken: null }),
    }),
    { name: "vira-auth" }
  )
);
