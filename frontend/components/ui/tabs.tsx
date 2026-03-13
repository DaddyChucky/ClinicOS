"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const tabs: Array<{ href: Route; label: string }> = [
  { href: "/", label: "Copilot" },
  { href: "/support", label: "Support" },
  { href: "/sales", label: "Sales & Outreach" },
  { href: "/marketing", label: "Marketing" },
  { href: "/review", label: "Review" }
];

export function TabsNav() {
  const pathname = usePathname();

  return (
    <nav className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
      {tabs.map((tab) => (
        <Link
          key={tab.href}
          href={tab.href}
          className={cn(
            "rounded-lg border px-3 py-2 text-center text-sm font-semibold transition",
            pathname === tab.href
              ? "border-transparent bg-accent text-white shadow-soft"
              : "border-slate-200 bg-white text-slate hover:border-slate-300 hover:bg-slate-50"
          )}
        >
          {tab.label}
        </Link>
      ))}
    </nav>
  );
}
