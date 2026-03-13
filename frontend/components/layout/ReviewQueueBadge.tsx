"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { QueueIcon } from "@/components/ui/icons";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export function ReviewQueueBadge() {
  const pathname = usePathname();
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    let active = true;

    async function refresh() {
      try {
        const queue = await api.listHumanSupportQueue();
        if (!active) return;
        setPendingCount(queue.filter((item) => item.handoff_stage === "queued").length);
      } catch {
        if (!active) return;
        setPendingCount(0);
      }
    }

    refresh();
    const interval = window.setInterval(refresh, 8000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  const active = pathname === "/admin/review" || pathname === "/admin/support";

  return (
    <Link
      href="/admin/review"
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-4 py-2.5 text-sm font-semibold transition",
        active
          ? "border-transparent bg-ink text-white shadow-[0_16px_36px_rgba(17,34,59,0.16)]"
          : "border-slate-200/80 bg-white/88 text-slate-700 hover:border-slate-300 hover:bg-white"
      )}
    >
      <QueueIcon className="h-4 w-4" />
      <span>Review Queue</span>
      {pendingCount > 0 ? (
        <span className="inline-flex min-w-6 items-center justify-center rounded-full bg-rose-500 px-1.5 py-0.5 text-[11px] font-semibold text-white shadow-[0_10px_22px_rgba(244,63,94,0.28)]">
          {pendingCount}
        </span>
      ) : null}
    </Link>
  );
}
