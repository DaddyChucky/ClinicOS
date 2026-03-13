import { TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={cn(
        "w-full rounded-[22px] border border-slate-200 bg-white/92 px-4 py-3 text-sm text-ink shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]",
        "outline-none ring-accent/30 transition focus:border-accent/60 focus:ring-4",
        "placeholder:text-slate-400",
        props.className
      )}
    />
  );
}
