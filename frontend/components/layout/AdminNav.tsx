"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";

import { ReviewQueueBadge } from "@/components/layout/ReviewQueueBadge";
import { ConsoleIcon, MarketingIcon, SalesIcon } from "@/components/ui/icons";
import { cn } from "@/lib/utils";

const links: Array<{ href: Route; label: string; icon: typeof ConsoleIcon }> = [
  { href: "/admin", label: "Operations Console", icon: ConsoleIcon },
  { href: "/admin/sales", label: "Sales & Outreach", icon: SalesIcon },
  { href: "/admin/marketing", label: "Marketing", icon: MarketingIcon },
];

export function AdminNav() {
  const pathname = usePathname();

  return (
    <nav className="grid grid-cols-2 gap-2 lg:flex lg:flex-wrap">
      {links.map((link, index) => {
        const active = pathname === link.href;
        const Icon = link.icon;
        return (
          <span key={link.href} className="contents">
            <Link
              href={link.href}
              className={cn(
                "inline-flex items-center justify-center gap-2 rounded-full border px-4 py-2.5 text-center text-sm font-semibold transition",
                active
                  ? "border-transparent bg-ink text-white shadow-[0_16px_36px_rgba(17,34,59,0.16)]"
                  : "border-slate-200/80 bg-white/88 text-slate-700 hover:border-slate-300 hover:bg-white"
              )}
            >
              <Icon className="h-4 w-4" />
              {link.label}
            </Link>
            {index === 0 ? <ReviewQueueBadge /> : null}
          </span>
        );
      })}
    </nav>
  );
}
