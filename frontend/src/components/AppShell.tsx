import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <span className="app-shell__brand">FounderShield&nbsp;AI</span>
        <span className="app-shell__tag">Privacy-first problem briefs</span>
      </header>
      <main className="app-shell__main">{children}</main>
      <footer className="app-shell__footer">
        <small>Your data stays private. Nothing is shared without your approval.</small>
      </footer>
    </div>
  );
}
