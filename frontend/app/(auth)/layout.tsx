/**
 * app/(auth)/layout.tsx
 *
 * Why this file exists:
 *   Auth pages get a centered, minimal layout — no sidebar, no chat
 *   shell. Route groups let this differ from (chat)/layout.tsx without
 *   affecting the URL.
 */

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg px-4">
      <div className="w-full max-w-sm">
        <h1 className="mb-8 text-center font-display text-3xl text-text">VIRA</h1>
        {children}
      </div>
    </div>
  );
}
