import { ButtonHTMLAttributes, PropsWithChildren } from "react";

import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "danger" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export function Button({ children, className, variant = "primary", ...props }: PropsWithChildren<ButtonProps>) {
  const variantClass =
    variant === "primary"
      ? "border border-transparent bg-accent text-white shadow-[0_18px_40px_rgba(13,118,104,0.22)] hover:-translate-y-0.5 hover:bg-accent-strong"
      : variant === "danger"
        ? "border border-transparent bg-danger text-white shadow-soft hover:-translate-y-0.5 hover:opacity-95"
        : variant === "ghost"
          ? "border border-transparent bg-transparent text-slate hover:bg-white/70 hover:text-ink"
          : "border border-slate-200/80 bg-white/88 text-ink shadow-[0_14px_30px_rgba(15,23,42,0.08)] hover:-translate-y-0.5 hover:border-slate-300 hover:bg-white";

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-full px-4 py-2.5 text-sm font-semibold transition duration-200",
        "disabled:cursor-not-allowed disabled:opacity-50",
        variantClass,
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
