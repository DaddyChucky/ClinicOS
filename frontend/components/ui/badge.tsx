import { PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

interface BadgeProps {
  className?: string;
  variant?: "default" | "success" | "warning" | "danger" | "info";
}

const variantClass: Record<NonNullable<BadgeProps["variant"]>, string> = {
  default: "bg-slate-100/90 text-slate",
  success: "bg-emerald-50 text-emerald-700",
  warning: "bg-amber-50 text-amber-700",
  danger: "bg-rose-50 text-rose-700",
  info: "bg-sky-50 text-sky-700"
};

export function Badge({ children, className, variant = "default" }: PropsWithChildren<BadgeProps>) {
  return (
    <span
      className={cn(
        "inline-flex rounded-full border border-white/70 px-2.5 py-1 text-xs font-semibold shadow-[inset_0_1px_0_rgba(255,255,255,0.65)]",
        variantClass[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
