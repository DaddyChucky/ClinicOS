import type { Metadata } from "next";
import Link from "next/link";
import { ReactNode } from "react";

import { AiModeBadge } from "@/components/layout/AiModeBadge";
import { AdminNav } from "@/components/layout/AdminNav";
import { PageShell } from "@/components/layout/PageShell";
import { Button } from "@/components/ui/button";
import { DeskIcon } from "@/components/ui/icons";

export const metadata: Metadata = {
  title: "Operations Console",
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

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <PageShell className="space-y-5">
      <header className="app-grid relative overflow-hidden rounded-[32px] border border-white/75 bg-[linear-gradient(120deg,rgba(219,234,254,0.88),rgba(255,255,255,0.96)_44%,rgba(220,252,231,0.82))] p-5 shadow-[0_24px_70px_rgba(15,23,42,0.08)] backdrop-blur-xl">
        <div className="relative space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Link href="/">
                <Button variant="ghost">
                  <ArrowLeftIcon />
                  Back
                </Button>
              </Link>
              <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">ClinicOS</p>
              <h1 className="text-3xl font-semibold tracking-[-0.03em] text-ink">Operations Console</h1>
              <p className="text-sm text-slate-700">Operational oversight for active conversations, specialist work, and human review.</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <AiModeBadge />
              <Link href="/workspace">
                <Button variant="secondary">
                  <DeskIcon className="h-4 w-4" />
                  Practice Desk
                </Button>
              </Link>
            </div>
          </div>
          <AdminNav />
        </div>
      </header>
      {children}
    </PageShell>
  );
}
