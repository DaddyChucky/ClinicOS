"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

function InfoIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true" className="h-4 w-4">
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10 8.1V13" stroke="currentColor" strokeLinecap="round" strokeWidth="1.5" />
      <circle cx="10" cy="6.2" r="0.9" fill="currentColor" />
    </svg>
  );
}

export function PmsInfoButton({ className }: { className?: string }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onMouseDown={(event) => event.preventDefault()}
        onClick={(event) => {
          event.preventDefault();
          event.stopPropagation();
          setOpen(true);
        }}
        className={cn(
          "inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 transition hover:border-emerald-200 hover:text-emerald-700",
          className
        )}
        aria-label="What counts as PMS or EHR?"
      >
        <InfoIcon />
      </button>

      <Dialog open={open} onClose={() => setOpen(false)} className="max-w-2xl">
        <div className="space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Practice Profile</p>
              <h3 className="text-2xl font-semibold tracking-[-0.03em] text-ink">What to list for PMS / EHR</h3>
            </div>
            <Button variant="ghost" className="px-3 py-2 text-xs" onClick={() => setOpen(false)}>
              Close
            </Button>
          </div>

          <div className="space-y-4 text-sm leading-7 text-slate-700">
            <p>
              Add the main system your practice uses to manage scheduling, charting, billing, or patient records. This can
              be a dental PMS, a medical EHR, or the core platform staff open first during the day.
            </p>
            <p>
              Helpful examples include Dentrix, Open Dental, Eaglesoft, athenahealth, eClinicalWorks, Epic, or a PMS plus
              EHR pair if your team truly works across both.
            </p>
            <p>
              ClinicOS AI uses this detail to tailor troubleshooting steps, rollout plans, and workflow recommendations to
              the systems your front desk and billing team actually use.
            </p>
          </div>
        </div>
      </Dialog>
    </>
  );
}
