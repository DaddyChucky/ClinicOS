"use client";

import { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

interface PowerSwitchProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  checked: boolean;
  label: string;
  description?: string;
}

export function PowerSwitch({ checked, label, description, className, ...props }: PowerSwitchProps) {
  return (
    <button
      type="button"
      className={cn(
        "flex w-full items-center justify-between gap-4 rounded-[24px] border px-4 py-4 text-left transition",
        checked
          ? "border-emerald-200 bg-[linear-gradient(180deg,rgba(236,253,245,0.98),rgba(255,255,255,0.98))] shadow-[0_18px_40px_rgba(5,150,105,0.14)]"
          : "border-rose-200 bg-[linear-gradient(180deg,rgba(255,241,242,0.98),rgba(255,255,255,0.98))] shadow-[0_18px_40px_rgba(225,29,72,0.12)]",
        className
      )}
      {...props}
    >
      <div className="space-y-1">
        <p className="text-sm font-semibold text-ink">{label}</p>
        {description ? <p className="text-sm leading-6 text-slate-600">{description}</p> : null}
      </div>
      <div className={cn("relative h-8 w-16 rounded-full transition", checked ? "bg-emerald-500" : "bg-rose-500")}>
        <span
          className={cn(
            "absolute top-1 h-6 w-6 rounded-full bg-white shadow-[0_8px_16px_rgba(15,23,42,0.18)] transition",
            checked ? "left-9" : "left-1"
          )}
        />
      </div>
    </button>
  );
}
