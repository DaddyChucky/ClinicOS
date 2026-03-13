import type { Metadata } from "next";
import Link from "next/link";
import type { Route } from "next";

import { PageShell } from "@/components/layout/PageShell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "ClinicOS",
};

const entryCards = [
  {
    eyebrow: "Client workspace",
    title: "Practice Desk",
    description:
      "Work with ClinicOS AI in a focused assistant workspace that carries conversation context, recommends next steps, and helps complete your practice profile over time.",
    href: "/workspace" as Route,
    cta: "Open Practice Desk",
    variant: "primary" as const,
  },
  {
    eyebrow: "Internal operations",
    title: "Operations Console",
    description:
      "Review escalations, inspect specialist workstreams, and monitor the operational state behind each active practice conversation.",
    href: "/admin" as Route,
    cta: "Open Operations Console",
    variant: "secondary" as const,
  },
];

export default function EntryPage() {
  return (
    <PageShell className="flex items-center">
      <div className="w-full space-y-8">
        <section className="app-grid relative overflow-hidden rounded-[38px] border border-white/70 bg-white/72 px-6 py-8 shadow-[0_30px_80px_rgba(15,23,42,0.1)] backdrop-blur-xl lg:px-10 lg:py-10">
          <div className="absolute inset-x-0 top-0 h-36 bg-gradient-to-b from-emerald-100/70 via-sky-50/60 to-transparent" />
          <div className="relative grid gap-8 lg:grid-cols-[minmax(0,1.2fr)_360px] lg:items-end">
            <div className="space-y-5 animate-fade-rise">
              <Badge variant="info" className="w-fit">
                ClinicOS
              </Badge>
              <div className="space-y-4">
                <h1 className="max-w-3xl text-4xl font-semibold tracking-[-0.03em] text-ink lg:text-6xl">
                  The operating system for modern dental and medical practices.
                </h1>
                <p className="max-w-2xl text-base leading-7 text-slate-700 lg:text-lg">
                  ClinicOS brings support, growth, and marketing work into one calm workspace so teams can resolve daily
                  issues faster and run the practice with more confidence.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 text-sm text-slate-600">
                <span className="rounded-full border border-white/80 bg-white/80 px-3 py-1.5">Persistent thread memory</span>
                <span className="rounded-full border border-white/80 bg-white/80 px-3 py-1.5">Mixed-intent operations guidance</span>
                <span className="rounded-full border border-white/80 bg-white/80 px-3 py-1.5">Human escalation when needed</span>
              </div>
            </div>

            <Card className="animate-fade-rise space-y-4 bg-[linear-gradient(180deg,rgba(255,255,255,0.94),rgba(240,248,246,0.92))]">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">Product view</p>
                <Badge variant="success">Live-ready</Badge>
              </div>
              <div className="space-y-3">
                <div className="rounded-[24px] border border-emerald-100 bg-white/90 p-4">
                  <p className="text-sm font-semibold text-ink">ClinicOS AI</p>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    Handles support questions, patient growth planning, and marketing requests in one connected thread.
                  </p>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
                  <div className="rounded-[22px] border border-slate-200/80 bg-slate-50/80 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Practice Desk</p>
                    <p className="mt-2 text-sm text-slate-700">Conversation-first workspace for practice teams.</p>
                  </div>
                  <div className="rounded-[22px] border border-slate-200/80 bg-slate-50/80 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Operations Console</p>
                    <p className="mt-2 text-sm text-slate-700">Operational oversight for specialists and reviewers.</p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </section>

        <section className="grid gap-5 xl:grid-cols-2">
          {entryCards.map((card, index) => (
            <Card
              key={card.title}
              className={`animate-fade-rise space-y-5 overflow-hidden p-6 lg:p-7 ${index === 0 ? "bg-white/88" : "bg-white/80"}`}
            >
              <div className="space-y-3">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{card.eyebrow}</p>
                <div className="space-y-2">
                  <h2 className="text-3xl font-semibold tracking-[-0.03em] text-ink">{card.title}</h2>
                  <p className="max-w-xl text-sm leading-6 text-slate-700">{card.description}</p>
                </div>
              </div>
              <div>
                <Link href={card.href}>
                  <Button variant={card.variant} className="w-full justify-between px-5">
                    {card.cta}
                    <span aria-hidden="true">→</span>
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </section>
      </div>
    </PageShell>
  );
}
