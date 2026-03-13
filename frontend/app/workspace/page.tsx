import type { Metadata } from "next";
import Link from "next/link";

import { ChatShell } from "@/components/chat/ChatShell";
import { PageShell } from "@/components/layout/PageShell";
import { Button } from "@/components/ui/button";
import { ConsoleIcon } from "@/components/ui/icons";

export const metadata: Metadata = {
  title: "Practice Desk",
};

function ArrowLeftIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" className="h-4 w-4">
      <path
        d="M11.75 4.5L6.25 10L11.75 15.5M6.75 10H16"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.6"
      />
    </svg>
  );
}

export default function WorkspacePage() {
  return (
    <PageShell className="space-y-6">
      <header className="app-grid relative overflow-hidden rounded-[32px] border border-white/75 bg-[linear-gradient(120deg,rgba(220,252,231,0.82),rgba(255,255,255,0.96)_42%,rgba(219,234,254,0.88))] p-4 shadow-[0_24px_70px_rgba(15,23,42,0.08)] backdrop-blur-xl lg:p-5">
        <div className="relative flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Link href="/">
              <Button variant="ghost" className="h-11 px-4">
                <ArrowLeftIcon />
                Back
              </Button>
            </Link>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">ClinicOS</p>
              <h1 className="text-2xl font-semibold tracking-[-0.03em] text-ink">Practice Desk</h1>
              <p className="text-sm text-slate-700">ClinicOS AI keeps clinic software support, billing help, and escalation routing in one clear chat.</p>
            </div>
          </div>

          <Link href="/admin">
            <Button variant="secondary" className="h-11 px-5">
              <ConsoleIcon className="h-4 w-4" />
              Operations Console
            </Button>
          </Link>
        </div>
      </header>

      <ChatShell />
    </PageShell>
  );
}
