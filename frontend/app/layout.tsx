/**
 * app/layout.tsx
 *
 * Why this file exists:
 *   Root layout wrapping every route: mounts QueryProvider (TanStack
 *   Query client) that every page needs for server-state fetching.
 */

import type { Metadata } from "next";
import { QueryProvider } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "VIRA",
  description: "Virtual Intelligent Responsive Assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="font-body antialiased">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
