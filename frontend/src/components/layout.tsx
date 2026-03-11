import type { ReactNode } from "react";

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b bg-white shadow-sm">
        <div className="px-4 py-4">
          <h1 className="text-2xl font-bold text-teal-800">Wool Stash</h1>
          <p className="text-sm text-stone-500">Helen's yarn catalogue</p>
        </div>
      </header>
      <main className="px-4 py-6">{children}</main>
    </div>
  );
}
